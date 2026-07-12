from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import dump_json_or_none, parse_json_or_none
from app.core.prompt_snapshot import build_prompt_snapshot, dump_prompt_snapshot, parse_prompt_snapshot
from app.core.scenarios import SCENARIO_TITLE_PREFIX
from app.core.system_settings import get_effective_digital_human_credit_costs, get_effective_digital_human_precharge_cost
from app.core.task_timeout import project_task_runtime_state
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import (
    calculate_user_credit_cost,
    charge_user_credits,
    get_user_credits,
    refund_user_credits,
)
from app.models import VideoTask
from app.schemas.response import fail, success
from app.services.digital_human_assets import get_available_audio_asset, get_enabled_voice, resolve_avatar
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate
from app.services.heygen_task_lifecycle import (
    clean_text,
    get_or_create_video_job,
    sync_video_job_status,
)

SCENARIO = "digital_human"
QUALITY_TIERS = {"standard", "premium"}
SUPPORTED_RESOLUTIONS = {"720p", "1080p"}
SUPPORTED_ASPECT_RATIOS = {"16:9", "9:16", "1:1"}


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


async def get_task_details(
    db: AsyncSession,
    *,
    task_id: str,
    user_id: int,
) -> dict | None:
    task = await get_task(db, task_id=task_id, user_id=user_id)
    if not task:
        return None
    payload = task_payload(task)
    payload["credits"] = await get_user_credits(db, user_id)
    return payload


async def archive_task(
    db: AsyncSession,
    *,
    task_id: str,
    user_id: int,
) -> str | None:
    task = await get_task(db, task_id=task_id, user_id=user_id)
    if not task:
        return "数字人视频不存在"

    task.archived = True
    task.archived_at = utc_now()
    await sync_job_status(db, task.job_id)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return "删除失败，请稍后重试"
    return None


def _default_title(script: str, audio_name: str | None) -> str:
    excerpt = clean_text(script).replace("\n", " ")[:20] or clean_text(audio_name)[:20]
    prefix = SCENARIO_TITLE_PREFIX.get(SCENARIO, "数字人")
    return f"{prefix}_{excerpt}" if excerpt else f"{prefix}_{utc_now():%Y%m%d_%H%M%S}"


def _settings_snapshot(*, avatar, voice, audio_asset, script, background_url, quality_tier, resolution, aspect_ratio, voice_speed) -> dict:
    audio_mode = "upload" if audio_asset else "platform"
    return {
        "scenario": SCENARIO,
        "media_type": "video",
        "language": voice.language if voice else "",
        "ratio": aspect_ratio,
        "quality": resolution,
        "scene": {
            "avatarId": avatar.avatar_id,
            "avatarName": avatar.name,
            "avatarPreviewImageUrl": avatar.preview_image_url,
            "avatarPreviewVideoUrl": avatar.preview_video_url,
            "avatarSource": avatar.source,
            "avatarAssetId": avatar.asset_id,
            "avatarType": avatar.avatar_type,
            "audioMode": audio_mode,
            "voiceId": voice.voice_id if voice else "",
            "voiceName": voice.name if voice else "",
            "voiceLanguage": voice.language if voice else "",
            "voicePreviewAudioUrl": voice.preview_audio_url if voice else "",
            "audioAssetId": audio_asset.id if audio_asset else "",
            "audioName": audio_asset.name if audio_asset else "",
            "audioUrl": audio_asset.audio_url if audio_asset else "",
            "audioDurationSeconds": int(audio_asset.duration_seconds or 0) if audio_asset else 0,
            "backgroundUrl": background_url,
            "script": script,
            "qualityTier": quality_tier,
            "resolution": resolution,
            "aspectRatio": aspect_ratio,
            "voiceSettings": {"speed": voice_speed} if audio_mode == "platform" else {},
        },
    }


async def create_task(
    db: AsyncSession,
    *,
    user_id: int,
    get_redis_pool,
    job_id: str | None,
    requested_title: str | None,
    avatar_id: str,
    voice_id: str | None,
    audio_asset_id: str | None,
    script: str | None,
    background_url: str | None,
    quality_tier: str,
    resolution: str,
    aspect_ratio: str,
    voice_speed: float,
):
    avatar_id = clean_text(avatar_id)
    voice_id = clean_text(voice_id)
    audio_asset_id = clean_text(audio_asset_id)
    script = clean_text(script)
    background_url = clean_text(background_url) or None
    quality_tier = clean_text(quality_tier) or "standard"
    resolution = clean_text(resolution) or "1080p"
    aspect_ratio = clean_text(aspect_ratio) or "9:16"
    try:
        voice_speed = round(float(voice_speed or 1), 2)
    except (TypeError, ValueError):
        voice_speed = 1.0
    if voice_speed <= 0:
        voice_speed = 1.0

    if not avatar_id:
        return fail("请选择数字人")
    if not voice_id and not audio_asset_id:
        return fail("请选择系统声音或上传音频")
    if voice_id and audio_asset_id:
        return fail("系统声音和上传音频不能同时使用")
    if quality_tier not in QUALITY_TIERS:
        return fail("不支持的生成档位")
    if resolution not in SUPPORTED_RESOLUTIONS:
        return fail("不支持的视频清晰度")
    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        return fail("不支持的视频比例")

    avatar = await resolve_avatar(db, avatar_id=avatar_id, user_id=user_id)
    if not avatar:
        return fail("数字人不存在或已停用")
    voice = None
    audio_asset = None
    if audio_asset_id:
        audio_asset = await get_available_audio_asset(db, audio_asset_id=audio_asset_id, user_id=user_id)
        if not audio_asset:
            return fail("上传音频不存在或已删除")
    else:
        voice = await get_enabled_voice(db, voice_id)
        if not voice:
            return fail("系统声音不存在或已停用")
        if not script:
            return fail("请输入口播文案")

    title = clean_text(requested_title) or _default_title(script, audio_asset.name if audio_asset else None)
    try:
        credit_cost = await get_effective_digital_human_precharge_cost(db, quality_tier)
    except ValueError as exc:
        return fail(str(exc))
    snapshot = _settings_snapshot(
        avatar=avatar,
        voice=voice,
        audio_asset=audio_asset,
        script=script,
        background_url=background_url,
        quality_tier=quality_tier,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        voice_speed=voice_speed,
    )
    job = await get_or_create_job(db, user_id=user_id, job_id=job_id, title=title, settings_snapshot=snapshot, script=script)
    if job_id and job is None:
        return fail("任务不存在")
    quality_label = "高质档" if quality_tier == "premium" else "标准档"
    charge, failure = await deduct_credits_or_fail(db, user_id, credit_cost, note=f"数字人 · {quality_label} · {title}")
    if failure is not None:
        return failure
    credit_cost = charge.cost
    remaining_credits = charge.balance_after
    snapshot["billing"] = {"consumption_multiplier": f"{charge.multiplier:.2f}"}

    prompt = script or f"自定义音频：{audio_asset.name}"
    task = VideoTask(
        id=str(uuid.uuid4()), user_id=user_id, job_id=job.id if job else None,
        scenario=SCENARIO, type_id=quality_tier, title=title, sort_order=0,
        prompt=prompt, input_mode="avatar", duration=0, resolution=resolution,
        aspect_ratio=aspect_ratio, status="pending", progress=10, provider="heygen",
        credit_cost=credit_cost,
        prompt_snapshot_json=dump_prompt_snapshot(build_prompt_snapshot(user=prompt, final=prompt)),
        settings_snapshot_json=dump_json_or_none(snapshot),
    )
    db.add(task)
    if job is not None:
        job.status = "generating"
        job.updated_at = utc_now()
    try:
        await db.commit()
        await db.refresh(task)
    except Exception:
        await db.rollback()
        return fail("数字人任务创建失败，请稍后重试")

    async def mark_failed(_refunded_credits: int) -> None:
        await db.execute(update(VideoTask).where(VideoTask.id == task.id).values(status="failed", progress=0, credit_refunded=True))

    enqueue_failure = await enqueue_or_compensate(
        get_redis_pool=get_redis_pool, db=db, job_name="submit_digital_human_task",
        job_args=(task.id,), user_id=user_id, credit_cost=credit_cost,
        remaining_credits=remaining_credits, refund_credits=refund_user_credits,
        mark_failed=mark_failed, failure_message="数字人任务入队失败，请稍后重试",
        failure_data={"task_id": task.id, "job_id": task.job_id},
        refund_note=f"数字人任务入队失败退回 · {task.id}",
    )
    if enqueue_failure is not None:
        return enqueue_failure
    return success({"task_id": task.id, "job_id": task.job_id, "provider_task_id": None, "status": "pending", "credits": remaining_credits, "credit_cost": credit_cost})


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

    snapshot = parse_json_or_none(task.settings_snapshot_json)
    multiplier = snapshot["billing"]["consumption_multiplier"]
    final_cost = calculate_user_credit_cost(int(per_second_cost) * duration, multiplier)
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
        await charge_user_credits(
            db,
            task.user_id,
            delta,
            note=f"数字人结算补扣 · {task.id}",
            multiplier="1.00",
            allow_negative=True,
        )
    task.credit_cost = final_cost
    return True
