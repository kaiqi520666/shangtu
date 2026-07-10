from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import parse_json_or_none
from app.core.prompt_snapshot import parse_prompt_snapshot
from app.core.providers.heygen_provider import get_video
from app.core.system_settings import get_effective_digital_human_credit_costs
from app.core.task_timeout import project_task_runtime_state
from app.core.time import to_utc_iso
from app.core.user_credits import deduct_user_credits_allow_negative, refund_user_credits
from app.models import VideoTask
from app.services.heygen_task_lifecycle import (
    clean_text,
    get_or_create_video_job,
    provider_task_status,
    refund_video_task_if_needed,
    sync_video_job_status,
    task_progress,
)

SCENARIO = "digital_human"


def should_sync_provider_task(task: VideoTask) -> bool:
    if not task.provider_task_id:
        return False
    if task.status not in {"done", "failed", "timeout"}:
        return True
    return task.status == "done" and int(task.duration or 0) < 1


def task_payload(task: VideoTask) -> dict:
    settings_snapshot = parse_json_or_none(task.settings_snapshot_json) or {}
    scene = settings_snapshot.get("scene") if isinstance(settings_snapshot.get("scene"), dict) else {}
    runtime = project_task_runtime_state(
        "video",
        status=task.status,
        error_message=task.error_message,
        progress=task.progress,
        result_url=task.result_url,
        created_at=task.created_at,
    )
    return {
        "task_id": task.id,
        "job_id": task.job_id,
        "scenario": task.scenario,
        "status": runtime.status,
        "progress": runtime.progress,
        "result_url": runtime.result_url,
        "title": task.title,
        "provider": task.provider,
        "provider_task_id": task.provider_task_id,
        "avatar_id": scene.get("avatarId"),
        "avatar_source": scene.get("avatarSource") or "system",
        "avatar_asset_id": scene.get("avatarAssetId"),
        "avatar_type": scene.get("avatarType"),
        "audio_mode": scene.get("audioMode") or "platform",
        "voice_id": scene.get("voiceId"),
        "audio_asset_id": scene.get("audioAssetId"),
        "audio_name": scene.get("audioName"),
        "audio_url": scene.get("audioUrl"),
        "audio_duration_seconds": scene.get("audioDurationSeconds"),
        "background_url": scene.get("backgroundUrl"),
        "script": scene.get("script"),
        "quality_tier": scene.get("qualityTier"),
        "voice_settings": scene.get("voiceSettings") or {},
        "prompt": task.prompt,
        "prompt_snapshot": parse_prompt_snapshot(task.prompt_snapshot_json),
        "settings_snapshot": settings_snapshot,
        "duration": task.duration,
        "resolution": task.resolution,
        "aspect_ratio": task.aspect_ratio,
        "credit_cost": task.credit_cost,
        "credit_refunded": bool(task.credit_refunded),
        "error_message": runtime.error_message,
        "created_at": to_utc_iso(task.created_at),
    }


async def get_or_create_job(
    db: AsyncSession,
    *,
    user_id: int,
    job_id: str | None,
    title: str,
    settings_snapshot: dict,
    script: str,
):
    return await get_or_create_video_job(
        db,
        user_id=user_id,
        job_id=job_id,
        scenario=SCENARIO,
        title=title,
        settings_snapshot=settings_snapshot,
        input_text=script,
    )


async def sync_job_status(db: AsyncSession, job_id: str | None) -> None:
    await sync_video_job_status(db, job_id=job_id, scenario=SCENARIO)


async def get_task(db: AsyncSession, *, task_id: str, user_id: int) -> VideoTask | None:
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == task_id,
            VideoTask.user_id == user_id,
            VideoTask.scenario == SCENARIO,
        )
    )
    return result.scalar_one_or_none()


def task_quality_tier(task: VideoTask) -> str:
    quality_tier = clean_text(task.type_id)
    if quality_tier:
        return quality_tier
    snapshot = parse_json_or_none(task.settings_snapshot_json) or {}
    scene = snapshot.get("scene") if isinstance(snapshot.get("scene"), dict) else {}
    return clean_text(scene.get("qualityTier")) or "standard"


async def settle_task_credits_if_needed(db: AsyncSession, task: VideoTask) -> bool:
    if task.scenario != SCENARIO or task.status != "done" or task.credit_refunded:
        return False
    duration = int(task.duration or 0)
    if duration < 1:
        return False
    try:
        costs = await get_effective_digital_human_credit_costs(db)
    except ValueError:
        return False
    per_second_cost = costs.get(task_quality_tier(task))
    if per_second_cost is None:
        return False

    final_cost = int(per_second_cost) * duration
    delta = final_cost - int(task.credit_cost or 0)
    if delta == 0:
        return False
    if delta < 0:
        await refund_user_credits(
            db,
            task.user_id,
            abs(delta),
            note=f"数字人结算退回 · {task.id}",
        )
    else:
        await deduct_user_credits_allow_negative(
            db,
            task.user_id,
            delta,
            note=f"数字人结算补扣 · {task.id}",
        )
    task.credit_cost = final_cost
    return True


async def sync_task_from_provider(db: AsyncSession, task: VideoTask) -> VideoTask:
    if not task.provider_task_id:
        return task
    async with httpx.AsyncClient(timeout=60) as client:
        data = await get_video(client, video_id=task.provider_task_id)

    video_url = clean_text(data.get("video_url") or data.get("url") or data.get("result_url")) or None
    error_message = clean_text(
        data.get("error_message") or data.get("failure_reason") or data.get("message")
    ) or None
    status = provider_task_status(
        clean_text(data.get("status") or data.get("video_status")),
        video_url=video_url,
        failure_message=error_message,
    )
    try:
        duration = max(0, int(float(data.get("duration") or data.get("video_duration") or 0)))
    except (TypeError, ValueError):
        duration = task.duration

    task.status = status
    task.progress = task_progress(status)
    task.result_url = video_url
    task.error_message = error_message
    task.duration = duration
    if status == "failed":
        await refund_video_task_if_needed(db, task, note=f"数字人任务失败退回 · {task.id}")
    elif status == "done":
        await settle_task_credits_if_needed(db, task)
    await sync_job_status(db, task.job_id)
    await db.commit()
    await db.refresh(task)
    return task
