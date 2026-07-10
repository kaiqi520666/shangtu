import logging
import os

import httpx
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.json_utils import parse_json_or_none
from app.core.oss import upload_audio_bytes
from app.core.time import utc_now
from app.core.user_credits import refund_user_credits
from app.models import GenerationJob, UserAudioAsset, VoiceoverTask

logger = logging.getLogger("app.worker.voiceover")


def provider_url() -> str:
    return os.getenv(
        "DASHSCOPE_TTS_URL",
        "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer",
    ).strip()


async def refund_task_if_needed(db, task: VoiceoverTask) -> int | None:
    if task.credit_refunded or task.credit_cost < 1:
        return None
    credits = await refund_user_credits(
        db,
        task.user_id,
        task.credit_cost,
        note=f"AI配音任务失败退回 · {task.id}",
    )
    task.credit_refunded = True
    return credits


async def mark_failed(task_id: str, message: str) -> None:
    async with SessionLocal() as db:
        task = (
            await db.execute(select(VoiceoverTask).where(VoiceoverTask.id == task_id).with_for_update())
        ).scalar_one_or_none()
        if not task or task.status == "done":
            return
        await refund_task_if_needed(db, task)
        task.status = "failed"
        task.progress = 0
        task.error_message = message
        job = await db.get(GenerationJob, task.job_id)
        if job:
            job.status = "failed"
        await db.commit()


async def generate_voiceover(ctx, task_id: str):
    async with SessionLocal() as db:
        task = (
            await db.execute(select(VoiceoverTask).where(VoiceoverTask.id == task_id).with_for_update())
        ).scalar_one_or_none()
        if not task or task.status != "pending":
            return
        task.status = "processing"
        task.progress = 20
        await db.commit()
        user_id = task.user_id
        text = task.text
        voice_id = task.voice_id
        rate = task.rate
        pitch = task.pitch
        volume = task.volume
        instruction = task.instruction
        settings = parse_json_or_none(task.settings_snapshot_json) or {}

    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        await mark_failed(task_id, "语音服务配置缺失")
        return
    payload = {
        "model": "cosyvoice-v3-flash",
        "input": {
            "text": text,
            "voice": voice_id,
            "format": "mp3",
            "sample_rate": 24000,
            "rate": rate,
            "pitch": pitch,
            "volume": volume,
        },
    }
    if instruction:
        payload["input"]["instruction"] = instruction

    try:
        async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
            response = await client.post(
                provider_url(),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            audio = (result.get("output") or {}).get("audio") or {}
            audio_url = audio.get("url")
            if not audio_url:
                raise RuntimeError("语音服务未返回音频")
            download = await client.get(audio_url)
            download.raise_for_status()
            if not download.content:
                raise RuntimeError("语音服务返回空音频")
            uploaded = await upload_audio_bytes(
                user_id=user_id,
                content=download.content,
                content_type="audio/mpeg",
                source="generated-audio",
            )
    except Exception as exc:
        logger.exception("Voiceover generation failed task=%s", task_id, exc_info=exc)
        await mark_failed(task_id, "AI配音生成失败，请稍后重试")
        return

    async with SessionLocal() as db:
        task = (
            await db.execute(select(VoiceoverTask).where(VoiceoverTask.id == task_id).with_for_update())
        ).scalar_one_or_none()
        if not task or task.status != "processing":
            return
        asset = UserAudioAsset(
            user_id=task.user_id,
            name=f"{settings.get('voice_name') or 'AI配音'}_{task.id[:8]}",
            audio_url=uploaded.url,
            object_key=uploaded.object_key,
            duration_seconds=0,
            size=uploaded.size,
            content_type="audio/mpeg",
            source="tts",
        )
        db.add(asset)
        await db.flush()
        task.result_asset_id = asset.id
        task.provider_request_id = result.get("request_id") or audio.get("id")
        task.usage_characters = (result.get("usage") or {}).get("characters")
        task.status = "done"
        task.progress = 100
        task.error_message = None
        task.updated_at = utc_now()
        job = await db.get(GenerationJob, task.job_id)
        if job:
            job.status = "done"
        await db.commit()
