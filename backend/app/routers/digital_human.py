from __future__ import annotations

import uuid

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import dump_json_or_none, parse_json_or_none
from app.core.pagination import page_payload
from app.core.prompt_snapshot import build_prompt_snapshot, dump_prompt_snapshot, parse_prompt_snapshot
from app.core.providers.heygen_provider import (
    create_avatar_video,
    get_video,
    parse_heygen_error_message,
)
from app.core.scenarios import SCENARIO_TITLE_PREFIX
from app.core.system_settings import (
    get_effective_digital_human_credit_costs,
    get_effective_digital_human_precharge_cost,
    get_effective_digital_human_precharge_costs,
)
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import (
    deduct_user_credits_allow_negative,
    get_user_credits,
    refund_user_credits,
)
from app.core.deps import get_current_user, get_db
from app.core.task_timeout import project_task_runtime_state
from app.models import GenerationJob, HeygenAvatar, HeygenVoice, User, VideoTask
from app.routers.admin.utils import heygen_avatar_payload, heygen_voice_payload
from app.schemas.response import Response, fail, success
from app.services.generation_tasks import deduct_credits_or_fail

router = APIRouter(prefix="/digital-human", tags=["数字人"])

QUALITY_TIER_TO_ENGINE = {
    "standard": "avatar_iii",
    "premium": "avatar_iv",
}
SUPPORTED_ASPECT_RATIOS = {"16:9", "9:16", "1:1"}
SUPPORTED_RESOLUTIONS = {"720p", "1080p"}
DEFAULT_RESOLUTION = "1080p"


class DigitalHumanVoiceSettings(BaseModel):
    speed: float = 1.0


class DigitalHumanBackground(BaseModel):
    url: str


class DigitalHumanGenerateRequest(BaseModel):
    job_id: str | None = None
    title: str | None = None
    avatar_id: str
    voice_id: str
    script: str
    background: DigitalHumanBackground | None = None
    quality_tier: str = "standard"
    resolution: str = DEFAULT_RESOLUTION
    aspect_ratio: str = "9:16"
    voice_settings: DigitalHumanVoiceSettings | None = None


def _clean_text(value: str | None) -> str:
    return str(value or "").strip()


def _default_job_title(script: str) -> str:
    prefix = SCENARIO_TITLE_PREFIX.get("digital_human", "数字人")
    excerpt = _clean_text(script).replace("\n", " ")[:20]
    if excerpt:
        return f"{prefix}_{excerpt}"
    return f"{prefix}_{utc_now():%Y%m%d_%H%M%S}"


def _task_status_from_provider(
    provider_status: str | None,
    *,
    video_url: str | None = None,
    failure_message: str | None = None,
) -> str:
    normalized = _clean_text(provider_status).lower()
    if video_url:
        return "done"
    if normalized in {"completed", "done", "success", "succeeded"}:
        return "done"
    if normalized in {"failed", "error", "canceled", "cancelled"} or failure_message:
        return "failed"
    if normalized in {"pending", "queued", "processing", "rendering", "in_progress"}:
        return "processing" if normalized != "pending" else "pending"
    return "processing"


def _task_progress_from_status(status: str) -> int:
    if status == "done":
        return 100
    if status == "failed":
        return 0
    if status == "processing":
        return 65
    return 10


def _normalize_voice_speed(value: float | int | None) -> float:
    try:
        speed = float(value or 1.0)
    except (TypeError, ValueError):
        return 1.0
    if speed <= 0:
        return 1.0
    return round(speed, 2)


def _digital_human_consume_note(*, quality_tier: str, title: str | None) -> str:
    quality_label = "高质档" if quality_tier == "premium" else "标准档"
    parts = ["数字人", quality_label]
    clean_title = _clean_text(title)
    if clean_title:
        parts.append(clean_title)
    return " · ".join(parts)


def _snapshot_scene(snapshot: dict | None) -> dict:
    if not isinstance(snapshot, dict):
        return {}
    scene = snapshot.get("scene")
    if isinstance(scene, dict):
        return scene
    return {}


def _task_quality_tier(task: VideoTask) -> str:
    quality_tier = _clean_text(task.type_id)
    if quality_tier:
        return quality_tier
    scene = _snapshot_scene(parse_json_or_none(task.settings_snapshot_json))
    return _clean_text(scene.get("qualityTier")) or "standard"


def _should_sync_provider_task(task: VideoTask) -> bool:
    if not task.provider_task_id:
        return False
    if task.status not in {"done", "failed", "timeout"}:
        return True
    return task.status == "done" and int(task.duration or 0) < 1


def _build_settings_snapshot(
    *,
    avatar: HeygenAvatar,
    voice: HeygenVoice,
    script: str,
    background_url: str | None,
    quality_tier: str,
    resolution: str,
    aspect_ratio: str,
    voice_settings: dict,
) -> dict:
    return {
        "scenario": "digital_human",
        "media_type": "video",
        "language": voice.language or "",
        "ratio": aspect_ratio,
        "quality": resolution,
        "scene": {
            "avatarId": avatar.avatar_id,
            "avatarName": avatar.name,
            "avatarPreviewImageUrl": avatar.preview_image_url,
            "voiceId": voice.voice_id,
            "voiceName": voice.name,
            "voiceLanguage": voice.language,
            "voicePreviewAudioUrl": voice.preview_audio_url,
            "backgroundUrl": background_url,
            "script": script,
            "qualityTier": quality_tier,
            "resolution": resolution,
            "aspectRatio": aspect_ratio,
            "voiceSettings": voice_settings,
        },
    }


async def _get_enabled_avatar(db: AsyncSession, avatar_id: str) -> HeygenAvatar | None:
    result = await db.execute(
        select(HeygenAvatar).where(
            HeygenAvatar.avatar_id == avatar_id,
            HeygenAvatar.enabled == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def _get_enabled_voice(db: AsyncSession, voice_id: str) -> HeygenVoice | None:
    result = await db.execute(
        select(HeygenVoice).where(
            HeygenVoice.voice_id == voice_id,
            HeygenVoice.enabled == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def _get_or_create_job(
    db: AsyncSession,
    *,
    current_user: User,
    job_id: str | None,
    title: str,
    settings_snapshot: dict,
    script: str,
) -> GenerationJob | None:
    if job_id:
        result = await db.execute(
            select(GenerationJob).where(
                GenerationJob.id == job_id,
                GenerationJob.user_id == current_user.id,
                GenerationJob.scenario == "digital_human",
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            return None
        job.title = title
        job.settings_json = dump_json_or_none(settings_snapshot)
        job.input_text = script
        job.updated_at = utc_now()
        return job

    job = GenerationJob(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        scenario="digital_human",
        title=title,
        status="draft",
        settings_json=dump_json_or_none(settings_snapshot),
        input_text=script,
    )
    db.add(job)
    return job


async def _sync_job_status(db: AsyncSession, job_id: str | None) -> None:
    if not job_id:
        return
    job_result = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        return

    task_result = await db.execute(
        select(VideoTask.status, VideoTask.result_url, VideoTask.error_message, VideoTask.created_at).where(
            VideoTask.job_id == job_id,
            VideoTask.archived == False,  # noqa: E712
            VideoTask.scenario == "digital_human",
        )
    )
    rows = task_result.all()
    if not rows:
        job.status = "draft"
        job.updated_at = utc_now()
        return

    total = len(rows)
    completed = 0
    failed = 0
    for status, result_url, error_message, created_at in rows:
        runtime = project_task_runtime_state(
            "video",
            status=status,
            error_message=error_message,
            progress=0,
            result_url=result_url,
            created_at=created_at,
        )
        if runtime.status == "done":
            completed += 1
        elif runtime.status in {"failed", "timeout"}:
            failed += 1

    if completed == total:
        job.status = "done"
    elif failed == total:
        job.status = "failed"
    elif completed > 0 or failed > 0:
        job.status = "generating"
    else:
        job.status = "generating"
    job.updated_at = utc_now()


def _digital_human_task_payload(task: VideoTask) -> dict:
    settings_snapshot = parse_json_or_none(task.settings_snapshot_json) or {}
    scene = _snapshot_scene(settings_snapshot)
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
        "voice_id": scene.get("voiceId"),
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


async def _get_task(
    db: AsyncSession,
    *,
    task_id: str,
    user_id: int,
) -> VideoTask | None:
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == task_id,
            VideoTask.user_id == user_id,
            VideoTask.scenario == "digital_human",
        )
    )
    return result.scalar_one_or_none()


async def _sync_task_from_provider(db: AsyncSession, task: VideoTask) -> VideoTask:
    if not task.provider_task_id:
        return task

    async with httpx.AsyncClient(timeout=60) as client:
        data = await get_video(client, video_id=task.provider_task_id)

    provider_status = _clean_text(
        str(data.get("status") or data.get("video_status") or "")
    )
    video_url = _clean_text(
        str(data.get("video_url") or data.get("url") or data.get("result_url") or "")
    ) or None
    error_message = _clean_text(
        str(
            data.get("error_message")
            or data.get("failure_reason")
            or data.get("message")
            or ""
        )
    ) or None
    local_status = _task_status_from_provider(
        provider_status,
        video_url=video_url,
        failure_message=error_message,
    )

    duration_value = data.get("duration") or data.get("video_duration") or 0
    try:
        duration = max(0, int(float(duration_value or 0)))
    except (TypeError, ValueError):
        duration = task.duration

    task.status = local_status
    task.progress = _task_progress_from_status(local_status)
    task.result_url = video_url
    task.error_message = error_message
    task.duration = duration
    if local_status == "failed":
        await _refund_task_credits_if_needed(
            db,
            task,
            note=f"数字人任务失败退回 · {task.id}",
        )
    elif local_status == "done":
        await _settle_task_credits_if_needed(db, task)

    await _sync_job_status(db, task.job_id)
    await db.commit()
    await db.refresh(task)
    return task


async def _refund_task_credits_if_needed(
    db: AsyncSession,
    task: VideoTask,
    *,
    note: str,
) -> int | None:
    if task.credit_refunded or int(task.credit_cost or 0) <= 0:
        return None
    refunded_credits = await refund_user_credits(db, task.user_id, int(task.credit_cost), note=note)
    task.credit_refunded = True
    return refunded_credits


async def _settle_task_credits_if_needed(db: AsyncSession, task: VideoTask) -> bool:
    if task.scenario != "digital_human" or task.status != "done" or task.credit_refunded:
        return False

    duration = int(task.duration or 0)
    if duration < 1:
        return False

    try:
        costs = await get_effective_digital_human_credit_costs(db)
    except ValueError:
        return False

    quality_tier = _task_quality_tier(task)
    per_second_cost = costs.get(quality_tier)
    if per_second_cost is None:
        return False

    final_cost = int(per_second_cost) * duration
    current_cost = int(task.credit_cost or 0)
    delta = final_cost - current_cost
    if delta == 0:
        return False

    if delta < 0:
        await refund_user_credits(
            db,
            task.user_id,
            abs(delta),
            note=f"数字人结算退回 · {task.id}",
        )
        task.credit_cost = final_cost
        return True

    await deduct_user_credits_allow_negative(
        db,
        task.user_id,
        delta,
        note=f"数字人结算补扣 · {task.id}",
    )
    task.credit_cost = final_cost
    return True


@router.get("/avatars", response_model=Response)
async def list_digital_human_avatars(
    page: int = 1,
    page_size: int = 24,
    gender: str | None = None,
    orientation: str | None = None,
    engine: str | None = None,
    keyword: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = [HeygenAvatar.enabled == True]  # noqa: E712
    if gender in {"male", "female"}:
        conditions.append(func.lower(HeygenAvatar.gender) == gender)
    if orientation in {"portrait", "landscape"}:
        conditions.append(HeygenAvatar.preferred_orientation == orientation)
    if engine in {"avatar_iii", "avatar_iv", "avatar_v"}:
        conditions.append(HeygenAvatar.supported_api_engines_json.ilike(f'%"{engine}"%'))
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                HeygenAvatar.name.ilike(like),
                HeygenAvatar.avatar_id.ilike(like),
                HeygenAvatar.group_id.ilike(like),
            )
        )

    total_stmt = select(func.count()).select_from(HeygenAvatar)
    data_stmt = select(HeygenAvatar).order_by(
        HeygenAvatar.sort_order.asc(),
        HeygenAvatar.updated_at.desc(),
        HeygenAvatar.id.desc(),
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)

    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [heygen_avatar_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, page, page_size))


@router.get("/voices", response_model=Response)
async def list_digital_human_voices(
    page: int = 1,
    page_size: int = 24,
    gender: str | None = None,
    language: str | None = None,
    support_locale: str | None = None,
    keyword: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = [HeygenVoice.enabled == True]  # noqa: E712
    if gender in {"male", "female", "unknown"}:
        conditions.append(func.lower(HeygenVoice.gender) == gender)
    if language:
        if language == "__multilingual__":
            conditions.append(HeygenVoice.language == "Multilingual")
        else:
            conditions.append(HeygenVoice.language == language)
    if support_locale in {"true", "false"}:
        conditions.append(HeygenVoice.support_locale == (support_locale == "true"))
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                HeygenVoice.name.ilike(like),
                HeygenVoice.voice_id.ilike(like),
                HeygenVoice.language.ilike(like),
            )
        )

    total_stmt = select(func.count()).select_from(HeygenVoice)
    data_stmt = select(HeygenVoice).order_by(
        HeygenVoice.sort_order.asc(),
        HeygenVoice.updated_at.desc(),
        HeygenVoice.id.desc(),
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)

    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [heygen_voice_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, page, page_size))


@router.get("/config", response_model=Response)
async def get_digital_human_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user
    try:
        credit_costs = await get_effective_digital_human_credit_costs(db)
        precharge_costs = await get_effective_digital_human_precharge_costs(db)
    except ValueError as exc:
        return fail(str(exc))
    return success(
        {
            "credit_costs": credit_costs,
            "precharge_costs": precharge_costs,
        }
    )


@router.post("/tasks", response_model=Response)
async def create_digital_human_task(
    req: DigitalHumanGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    avatar_id = _clean_text(req.avatar_id)
    voice_id = _clean_text(req.voice_id)
    script = _clean_text(req.script)
    background_url = _clean_text(req.background.url if req.background else None) or None
    quality_tier = _clean_text(req.quality_tier) or "standard"
    resolution = _clean_text(req.resolution) or DEFAULT_RESOLUTION
    aspect_ratio = _clean_text(req.aspect_ratio) or "9:16"
    voice_settings = {
        "speed": _normalize_voice_speed(req.voice_settings.speed if req.voice_settings else 1.0),
    }

    if not avatar_id:
        return fail("请选择系统数字人")
    if not voice_id:
        return fail("请选择系统声音")
    if not script:
        return fail("请输入口播文案")
    if quality_tier not in QUALITY_TIER_TO_ENGINE:
        return fail("不支持的生成档位")
    if resolution not in SUPPORTED_RESOLUTIONS:
        return fail("不支持的视频清晰度")
    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        return fail("不支持的视频比例")

    avatar = await _get_enabled_avatar(db, avatar_id)
    if not avatar:
        return fail("系统数字人不存在或已停用")
    voice = await _get_enabled_voice(db, voice_id)
    if not voice:
        return fail("系统声音不存在或已停用")

    title = _clean_text(req.title) or _default_job_title(script)
    try:
        credit_cost = await get_effective_digital_human_precharge_cost(db, quality_tier)
    except ValueError as exc:
        return fail(str(exc))
    settings_snapshot = _build_settings_snapshot(
        avatar=avatar,
        voice=voice,
        script=script,
        background_url=background_url,
        quality_tier=quality_tier,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        voice_settings=voice_settings,
    )

    job = await _get_or_create_job(
        db,
        current_user=current_user,
        job_id=req.job_id,
        title=title,
        settings_snapshot=settings_snapshot,
        script=script,
    )
    if req.job_id and job is None:
        return fail("任务不存在")
    remaining_credits, fail_response = await deduct_credits_or_fail(
        db,
        current_user.id,
        credit_cost,
        note=_digital_human_consume_note(quality_tier=quality_tier, title=title),
    )
    if fail_response is not None:
        return fail_response

    task = VideoTask(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        job_id=job.id if job else None,
        scenario="digital_human",
        type_id=quality_tier,
        title=title,
        sort_order=0,
        prompt=script,
        input_mode="avatar",
        input_images_json=None,
        input_video_url=None,
        audio_setting=None,
        duration=0,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        status="pending",
        progress=10,
        provider="heygen",
        provider_task_id=None,
        credit_cost=credit_cost,
        prompt_snapshot_json=dump_prompt_snapshot(
            build_prompt_snapshot(
                user=script,
                final=script,
            )
        ),
        settings_snapshot_json=dump_json_or_none(settings_snapshot),
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

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            provider_data = await create_avatar_video(
                client,
                avatar_id=avatar.avatar_id,
                title=title,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                script=script,
                voice_id=voice.voice_id,
                engine_type=QUALITY_TIER_TO_ENGINE[quality_tier],
                background_url=background_url,
                voice_settings=voice_settings,
                idempotency_key=task.id,
            )
        provider_task_id = _clean_text(str(provider_data.get("video_id") or ""))
        if not provider_task_id:
            raise ValueError("HeyGen 未返回 video_id")
        task.provider_task_id = provider_task_id
        task.status = _task_status_from_provider(
            _clean_text(str(provider_data.get("status") or "")),
        )
        task.progress = _task_progress_from_status(task.status)
        provider_error_message = _clean_text(
            str(
                provider_data.get("error_message")
                or provider_data.get("failure_reason")
                or provider_data.get("message")
                or ""
            )
        ) or None
        if provider_error_message:
            task.error_message = provider_error_message
        refunded_credits = None
        if task.status == "failed":
            refunded_credits = await _refund_task_credits_if_needed(
                db,
                task,
                note=f"数字人任务失败退回 · {task.id}",
            )
        await _sync_job_status(db, task.job_id)
        await db.commit()
        await db.refresh(task)
        if task.status == "failed":
            latest_credits = refunded_credits
            if latest_credits is None:
                latest_credits = await get_user_credits(db, current_user.id)
            return fail(
                task.error_message or "HeyGen 任务创建失败，请稍后重试",
                data={
                    "task_id": task.id,
                    "job_id": task.job_id,
                    "credits": latest_credits,
                    "credit_cost": credit_cost,
                },
            )
    except ValueError as exc:
        task.status = "failed"
        task.progress = 0
        task.error_message = str(exc)
        refunded_credits = await _refund_task_credits_if_needed(
            db,
            task,
            note=f"数字人任务创建失败退回 · {task.id}",
        )
        await _sync_job_status(db, task.job_id)
        await db.commit()
        latest_credits = refunded_credits
        if latest_credits is None:
            latest_credits = await get_user_credits(db, current_user.id)
        return fail(
            str(exc),
            data={
                "task_id": task.id,
                "job_id": task.job_id,
                "credits": latest_credits,
                "credit_cost": credit_cost,
            },
        )
    except httpx.HTTPError as exc:
        message = parse_heygen_error_message(exc)
        task.status = "failed"
        task.progress = 0
        task.error_message = message
        refunded_credits = await _refund_task_credits_if_needed(
            db,
            task,
            note=f"数字人任务创建失败退回 · {task.id}",
        )
        await _sync_job_status(db, task.job_id)
        await db.commit()
        latest_credits = refunded_credits
        if latest_credits is None:
            latest_credits = await get_user_credits(db, current_user.id)
        return fail(
            message,
            data={
                "task_id": task.id,
                "job_id": task.job_id,
                "credits": latest_credits,
                "credit_cost": credit_cost,
            },
        )
    except Exception:
        task.status = "failed"
        task.progress = 0
        task.error_message = "HeyGen 任务创建失败，请稍后重试"
        refunded_credits = await _refund_task_credits_if_needed(
            db,
            task,
            note=f"数字人任务创建失败退回 · {task.id}",
        )
        await _sync_job_status(db, task.job_id)
        await db.commit()
        latest_credits = refunded_credits
        if latest_credits is None:
            latest_credits = await get_user_credits(db, current_user.id)
        return fail(
            "HeyGen 任务创建失败，请稍后重试",
            data={
                "task_id": task.id,
                "job_id": task.job_id,
                "credits": latest_credits,
                "credit_cost": credit_cost,
            },
        )

    return success(
        {
            "task_id": task.id,
            "job_id": task.job_id,
            "provider_task_id": task.provider_task_id,
            "status": task.status,
            "credits": remaining_credits,
            "credit_cost": credit_cost,
        }
    )


@router.get("/tasks/{task_id}", response_model=Response)
async def get_digital_human_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("数字人任务不存在")
    if _should_sync_provider_task(task):
        try:
            task = await _sync_task_from_provider(db, task)
        except httpx.HTTPError as exc:
            return fail(parse_heygen_error_message(exc))
        except Exception:
            return fail("HeyGen 任务查询失败，请稍后重试")
    if await _settle_task_credits_if_needed(db, task):
        await _sync_job_status(db, task.job_id)
        await db.commit()
        await db.refresh(task)
    payload = _digital_human_task_payload(task)
    payload["credits"] = await get_user_credits(db, current_user.id)
    return success(payload)


@router.delete("/tasks/{task_id}", response_model=Response)
async def delete_digital_human_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("数字人视频不存在")

    task.archived = True
    task.archived_at = utc_now()
    await _sync_job_status(db, task.job_id)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("删除失败，请稍后重试")

    return success({"task_id": task_id})


@router.get("/tasks/{task_id}/download")
async def download_digital_human_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task or not task.result_url:
        return fail("数字人视频不存在或尚未生成完成")

    async def stream():
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("GET", task.result_url) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk

    url_lower = task.result_url.lower()
    if url_lower.endswith(".webm"):
        media_type = "video/webm"
        ext = "webm"
    elif url_lower.endswith(".mov"):
        media_type = "video/quicktime"
        ext = "mov"
    else:
        media_type = "video/mp4"
        ext = "mp4"

    return StreamingResponse(
        stream(),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{task_id}.{ext}"'},
    )


@router.get("/tasks/{task_id}/poll", response_model=Response)
async def poll_digital_human_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("数字人任务不存在")
    if _should_sync_provider_task(task):
        try:
            task = await _sync_task_from_provider(db, task)
        except ValueError as exc:
            task.status = "failed"
            task.progress = 0
            task.error_message = str(exc)
            await _sync_job_status(db, task.job_id)
            await db.commit()
            await db.refresh(task)
        except httpx.HTTPError as exc:
            return fail(parse_heygen_error_message(exc))
        except Exception:
            return fail("HeyGen 任务查询失败，请稍后重试")
    elif await _settle_task_credits_if_needed(db, task):
        await _sync_job_status(db, task.job_id)
        await db.commit()
        await db.refresh(task)
    payload = _digital_human_task_payload(task)
    payload["credits"] = await get_user_credits(db, current_user.id)
    return success(payload)
