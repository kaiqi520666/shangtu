from __future__ import annotations

import mimetypes
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.media_download import remote_media_download_response
from app.core.oss import OssConfigError, upload_audio_bytes, upload_image_bytes
from app.core.pagination import page_payload
from app.core.providers.heygen_provider import (
    create_photo_avatar,
    parse_heygen_error_message,
)
from app.core.system_settings import (
    get_effective_digital_human_credit_costs,
    get_effective_digital_human_precharge_costs,
)
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import get_user_credits
from app.core.deps import get_current_user, get_db
from app.models import (
    HeygenAvatar,
    HeygenVoice,
    User,
    UserAudioAsset,
    UserAvatar,
    UserAvatarTask,
)
from app.routers.admin.utils import heygen_avatar_payload, heygen_voice_payload
from app.schemas.response import Response, fail, success
from app.services.digital_human import (
    create_task as _create_task,
    get_task as _get_task,
    sync_job_status as _sync_job_status,
    task_payload as _digital_human_task_payload,
)
from app.services.digital_human_assets import (
    extract_provider_avatar_identity as _extract_provider_avatar_identity,
    extract_provider_avatar_error_message as _extract_provider_avatar_error_message,
    extract_provider_avatar_status as _extract_provider_avatar_status,
    extract_provider_avatar_urls as _extract_provider_avatar_urls,
    get_available_audio_asset as _get_available_audio_asset,
    get_photo_avatar_asset as _get_photo_avatar_asset,
    get_user_avatar_task as _get_user_avatar_task,
    get_user_avatars_by_ids as _get_user_avatars_by_ids,
    provider_avatar_status as _provider_avatar_status,
    refund_user_avatar_task_if_needed as _refund_user_avatar_task_if_needed,
    sync_user_avatar_task_from_provider as _sync_user_avatar_task_from_provider,
    upsert_user_avatar_from_task as _upsert_user_avatar_from_task,
    user_avatar_payload as _user_avatar_payload,
    user_avatar_task_payload as _user_avatar_task_payload,
)
from app.services.heygen_task_lifecycle import (
    clean_text as _clean_text,
)

router = APIRouter(prefix="/digital-human", tags=["数字人"])

DEFAULT_RESOLUTION = "1080p"
PHOTO_AVATAR_TYPE = "photo"


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


def _clean_avatar_name(value: str | None, fallback: str = "照片数字人") -> str:
    cleaned = str(value or "").strip()
    if cleaned:
        return cleaned[:120]
    return fallback


def _audio_asset_payload(asset: UserAudioAsset) -> dict:
    return {
        "id": asset.id,
        "name": asset.name,
        "audio_url": asset.audio_url,
        "object_key": asset.object_key,
        "duration_seconds": int(asset.duration_seconds or 0),
        "size": int(asset.size or 0),
        "content_type": asset.content_type,
        "source": asset.source,
        "enabled": bool(asset.enabled),
        "created_at": to_utc_iso(asset.created_at),
        "updated_at": to_utc_iso(asset.updated_at),
    }


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
    asset = await _get_available_audio_asset(
        db,
        audio_asset_id=audio_asset_id,
        user_id=current_user.id,
    )
    if not asset:
        return fail("音频不存在")

    asset.enabled = False
    asset.archived_at = utc_now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("删除失败，请稍后重试")

    return success({"id": audio_asset_id})


@router.post("/photo-avatars/upload", response_model=Response)
async def upload_photo_avatar(
    file: UploadFile = File(...),
    name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not _clean_text(name):
        return fail("请输入数字人名称")
    avatar_name = _clean_avatar_name(name)
    uploaded = None
    detected_content_type = (file.content_type or "").strip()
    if not detected_content_type and file.filename:
        detected_content_type = mimetypes.guess_type(file.filename)[0] or ""

    try:
        content = await file.read()
        uploaded = await upload_image_bytes(
            user_id=current_user.id,
            content=content,
            content_type=detected_content_type,
            source="photo-avatars",
        )
    except (ValueError, OssConfigError) as exc:
        await db.rollback()
        return fail(str(exc))
    except Exception:
        await db.rollback()
        return fail("照片上传失败，请稍后重试")
    finally:
        await file.close()

    task = UserAvatarTask(
        user_id=current_user.id,
        avatar_type=PHOTO_AVATAR_TYPE,
        name=avatar_name,
        source_image_url=uploaded.url,
        source_object_key=uploaded.object_key,
        provider="heygen",
        status="pending",
        credit_cost=0,
        credit_refunded=False,
    )
    db.add(task)
    try:
        await db.commit()
        await db.refresh(task)
    except Exception:
        await db.rollback()
        return fail("照片数字人任务创建失败，请稍后重试")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            provider_data = await create_photo_avatar(
                client,
                name=avatar_name,
                image_url=uploaded.url,
                idempotency_key=task.id,
            )
        provider_task_id, provider_avatar_id = _extract_provider_avatar_identity(provider_data)
        if not provider_avatar_id:
            raise ValueError("HeyGen 未返回照片数字人 ID")
        task.provider_task_id = provider_task_id or provider_avatar_id
        task.provider_avatar_id = provider_avatar_id
        task.status = _provider_avatar_status(_extract_provider_avatar_status(provider_data))
        if task.status == "done":
            preview_image_url, preview_video_url = _extract_provider_avatar_urls(provider_data)
            asset = await _upsert_user_avatar_from_task(
                db,
                task=task,
                heygen_avatar_id=provider_avatar_id,
                preview_image_url=preview_image_url,
                preview_video_url=preview_video_url,
            )
            await db.flush()
            task.result_avatar_id = asset.id
        elif task.status == "failed":
            task.error_message = (
                _extract_provider_avatar_error_message(provider_data)
                or "HeyGen 创建失败，请稍后重试"
            )
            await _refund_user_avatar_task_if_needed(
                db,
                task,
                note=f"照片数字人创建失败退回 · {task.id}",
            )
        await db.commit()
        await db.refresh(task)
    except ValueError as exc:
        task.status = "failed"
        task.error_message = str(exc)
        refunded_credits = await _refund_user_avatar_task_if_needed(
            db,
            task,
            note=f"照片数字人创建失败退回 · {task.id}",
        )
        await db.commit()
        return fail(
            str(exc),
            data={
                "task_id": task.id,
                "credits": refunded_credits if refunded_credits is not None else await get_user_credits(db, current_user.id),
                "credit_cost": credit_cost,
            },
        )
    except httpx.HTTPError as exc:
        message = parse_heygen_error_message(exc)
        task.status = "failed"
        task.error_message = message
        refunded_credits = await _refund_user_avatar_task_if_needed(
            db,
            task,
            note=f"照片数字人创建失败退回 · {task.id}",
        )
        await db.commit()
        return fail(
            message,
            data={
                "task_id": task.id,
                "credits": refunded_credits if refunded_credits is not None else await get_user_credits(db, current_user.id),
                "credit_cost": credit_cost,
            },
        )
    except Exception:
        task.status = "failed"
        task.error_message = "HeyGen 创建失败，请稍后重试"
        refunded_credits = await _refund_user_avatar_task_if_needed(
            db,
            task,
            note=f"照片数字人创建失败退回 · {task.id}",
        )
        await db.commit()
        return fail(
            "HeyGen 创建失败，请稍后重试",
            data={
                "task_id": task.id,
                "credits": refunded_credits if refunded_credits is not None else await get_user_credits(db, current_user.id),
                "credit_cost": credit_cost,
            },
        )

    asset_map = await _get_user_avatars_by_ids(db, [task.result_avatar_id or ""])
    payload = _user_avatar_task_payload(task, asset_map.get(task.result_avatar_id or ""))
    payload["credits"] = await get_user_credits(db, current_user.id) if task.credit_refunded else remaining_credits
    return success(payload)


@router.get("/photo-avatars/tasks", response_model=Response)
async def list_photo_avatar_tasks(
    page: int = 1,
    page_size: int = 12,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 50)
    conditions = [
        UserAvatarTask.user_id == current_user.id,
        UserAvatarTask.archived_at.is_(None),
        UserAvatarTask.avatar_type == PHOTO_AVATAR_TYPE,
    ]

    total_stmt = select(func.count()).select_from(UserAvatarTask)
    data_stmt = select(UserAvatarTask).order_by(
        UserAvatarTask.created_at.desc(),
        UserAvatarTask.id.desc(),
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)

    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    tasks = result.scalars().all()
    asset_map = await _get_user_avatars_by_ids(db, [item.result_avatar_id or "" for item in tasks])
    items = [_user_avatar_task_payload(item, asset_map.get(item.result_avatar_id or "")) for item in tasks]
    return success(page_payload(items, total, page, page_size))


@router.get("/photo-avatars/tasks/{task_id}/poll", response_model=Response)
async def poll_photo_avatar_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_avatar_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("照片数字人任务不存在")
    if task.status in {"pending", "processing"} or (task.status == "done" and not task.result_avatar_id):
        try:
            task = await _sync_user_avatar_task_from_provider(db, task)
        except ValueError as exc:
            task.status = "failed"
            task.error_message = str(exc)
            await _refund_user_avatar_task_if_needed(
                db,
                task,
                note=f"照片数字人创建失败退回 · {task.id}",
            )
            await db.commit()
            await db.refresh(task)
        except httpx.HTTPError as exc:
            return fail(parse_heygen_error_message(exc))
        except Exception:
            return fail("HeyGen 状态查询失败，请稍后重试")
    asset_map = await _get_user_avatars_by_ids(db, [task.result_avatar_id or ""])
    payload = _user_avatar_task_payload(task, asset_map.get(task.result_avatar_id or ""))
    payload["credits"] = await get_user_credits(db, current_user.id)
    return success(payload)


@router.delete("/photo-avatars/tasks/{task_id}", response_model=Response)
async def delete_photo_avatar_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_avatar_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("照片数字人任务不存在")
    if task.status != "failed":
        return fail("仅支持删除创建失败的任务")

    task.archived_at = utc_now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("删除失败，请稍后重试")

    return success({"id": task_id})


@router.get("/photo-avatars", response_model=Response)
async def list_photo_avatars(
    page: int = 1,
    page_size: int = 12,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 50)
    conditions = [
        UserAvatar.user_id == current_user.id,
        UserAvatar.avatar_type == PHOTO_AVATAR_TYPE,
        UserAvatar.enabled == True,  # noqa: E712
        UserAvatar.status == "active",
        UserAvatar.archived_at.is_(None),
    ]

    total_stmt = select(func.count()).select_from(UserAvatar)
    data_stmt = select(UserAvatar).order_by(
        UserAvatar.created_at.desc(),
        UserAvatar.id.desc(),
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)

    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [_user_avatar_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, page, page_size))


@router.delete("/photo-avatars/{asset_id}", response_model=Response)
async def delete_photo_avatar(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    asset = await _get_photo_avatar_asset(
        db,
        asset_id=asset_id,
        user_id=current_user.id,
    )
    if not asset:
        return fail("照片数字人不存在")

    asset.enabled = False
    asset.status = "deleted"
    asset.archived_at = utc_now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("删除失败，请稍后重试")

    return success({"id": asset_id})


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
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("数字人任务不存在")
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
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("数字人任务不存在")
    payload = _digital_human_task_payload(task)
    payload["credits"] = await get_user_credits(db, current_user.id)
    return success(payload)
