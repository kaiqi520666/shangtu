from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.media_download import remote_media_download_response
from app.core.oss import OssConfigError, upload_audio_bytes
from app.core.pagination import page_payload
from app.core.system_settings import (
    get_effective_digital_human_credit_costs,
    get_effective_digital_human_precharge_costs,
)
from app.core.time import utc_now
from app.core.deps import get_current_user, get_db
from app.models import (
    HeygenAvatar,
    HeygenVoice,
    User,
    UserAudioAsset,
)
from app.routers.admin.utils import heygen_avatar_payload, heygen_voice_payload
from app.routers.photo_avatar import router as photo_avatar_router
from app.schemas.response import Response, fail, success
from app.services.digital_human import (
    archive_task as _archive_task,
    create_task as _create_task,
    get_task as _get_task,
    get_task_details as _get_task_details,
)
from app.services.digital_human_audio import (
    archive_audio_asset as _archive_audio_asset,
    audio_asset_payload as _audio_asset_payload,
)

router = APIRouter(prefix="/digital-human", tags=["数字人"])
router.include_router(photo_avatar_router)

DEFAULT_RESOLUTION = "1080p"


class DigitalHumanVoiceSettings(BaseModel):
    speed: float = 1.0


class DigitalHumanBackground(BaseModel):
    url: str


class DigitalHumanGenerateRequest(BaseModel):
    job_id: str | None = None
    title: str | None = None
    avatar_id: str
    voice_id: str | None = None
    audio_asset_id: str | None = None
    script: str | None = None
    background: DigitalHumanBackground | None = None
    quality_tier: str = "standard"
    resolution: str = DEFAULT_RESOLUTION
    aspect_ratio: str = "9:16"
    voice_settings: DigitalHumanVoiceSettings | None = None


def _normalize_duration_seconds(value: float | int | None) -> int:
    try:
        duration = float(value or 0)
    except (TypeError, ValueError):
        return 0
    if duration <= 0:
        return 0
    return int(round(duration))


def _clean_audio_asset_name(filename: str | None) -> str:
    stem = Path(str(filename or "").strip()).stem.strip()
    if stem:
        return stem[:255]
    return f"音频_{utc_now():%Y%m%d_%H%M%S}"


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


@router.post("/audio-assets/upload", response_model=Response)
async def upload_digital_human_audio_asset(
    file: UploadFile = File(...),
    duration_seconds: float | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        detected_content_type = (file.content_type or "").strip()
        if not detected_content_type and file.filename:
            detected_content_type = mimetypes.guess_type(file.filename)[0] or ""
        content = await file.read()
        uploaded = await upload_audio_bytes(
            user_id=current_user.id,
            content=content,
            content_type=detected_content_type,
            source="audio-uploads",
        )
        asset = UserAudioAsset(
            user_id=current_user.id,
            name=_clean_audio_asset_name(file.filename),
            audio_url=uploaded.url,
            object_key=uploaded.object_key,
            duration_seconds=_normalize_duration_seconds(duration_seconds),
            size=uploaded.size,
            content_type=uploaded.content_type,
            source="upload",
            enabled=True,
        )
        db.add(asset)
        await db.commit()
        await db.refresh(asset)
    except (ValueError, OssConfigError) as exc:
        await db.rollback()
        return fail(str(exc))
    except Exception:
        await db.rollback()
        return fail("音频上传失败")
    finally:
        await file.close()

    return success(_audio_asset_payload(asset))


@router.get("/audio-assets", response_model=Response)
async def list_digital_human_audio_assets(
    page: int = 1,
    page_size: int = 12,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 50)
    conditions = [
        UserAudioAsset.user_id == current_user.id,
        UserAudioAsset.enabled == True,  # noqa: E712
        UserAudioAsset.archived_at.is_(None),
    ]

    total_stmt = select(func.count()).select_from(UserAudioAsset)
    data_stmt = select(UserAudioAsset).order_by(
        UserAudioAsset.created_at.desc(),
        UserAudioAsset.id.desc(),
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)

    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [_audio_asset_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, page, page_size))


@router.delete("/audio-assets/{audio_asset_id}", response_model=Response)
async def delete_digital_human_audio_asset(
    audio_asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    error_message = await _archive_audio_asset(
        db,
        audio_asset_id=audio_asset_id,
        user_id=current_user.id,
    )
    if error_message:
        return fail(error_message)
    return success({"id": audio_asset_id})




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
            "consumption_multiplier": float(current_user.consumption_multiplier),
        }
    )


@router.post("/tasks", response_model=Response)
async def create_digital_human_task(
    req: DigitalHumanGenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _create_task(
        db,
        user_id=current_user.id,
        get_redis_pool=lambda: request.app.state.redis_pool,
        job_id=req.job_id,
        requested_title=req.title,
        avatar_id=req.avatar_id,
        voice_id=req.voice_id,
        audio_asset_id=req.audio_asset_id,
        script=req.script,
        background_url=req.background.url if req.background else None,
        quality_tier=req.quality_tier,
        resolution=req.resolution,
        aspect_ratio=req.aspect_ratio,
        voice_speed=req.voice_settings.speed if req.voice_settings else 1.0,
    )


@router.get("/tasks/{task_id}", response_model=Response)
async def get_digital_human_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = await _get_task_details(db, task_id=task_id, user_id=current_user.id)
    if payload is None:
        return fail("数字人任务不存在")
    return success(payload)


@router.delete("/tasks/{task_id}", response_model=Response)
async def delete_digital_human_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    error_message = await _archive_task(
        db,
        task_id=task_id,
        user_id=current_user.id,
    )
    if error_message:
        return fail(error_message)
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

    return remote_media_download_response(
        task.result_url,
        filename_stem=task_id,
        fallback_extension="mp4",
    )


@router.get("/tasks/{task_id}/poll", response_model=Response)
async def poll_digital_human_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = await _get_task_details(db, task_id=task_id, user_id=current_user.id)
    if payload is None:
        return fail("数字人任务不存在")
    return success(payload)
