from __future__ import annotations

import httpx
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.providers.heygen_provider import get_avatar_look
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import refund_user_credits
from app.models import HeygenAvatar, HeygenVoice, UserAudioAsset, UserAvatar, UserAvatarTask
from app.services.heygen_task_lifecycle import clean_text


class ResolvedAvatar(BaseModel):
    avatar_id: str
    name: str
    preview_image_url: str = ""
    preview_video_url: str = ""
    source: str = "system"
    asset_id: str = ""
    avatar_type: str = "studio_avatar"


def provider_avatar_status(provider_status: str | None, *, failure_message: str | None = None) -> str:
    normalized = clean_text(provider_status).lower()
    if normalized in {"completed", "done", "success", "succeeded", "ready", "active"}:
        return "done"
    if normalized in {"failed", "error", "canceled", "cancelled", "rejected"} or failure_message:
        return "failed"
    if normalized == "pending":
        return "pending"
    return "processing"


def provider_avatar_progress(status: str) -> int:
    return {"done": 100, "failed": 0, "processing": 65}.get(status, 10)


def user_avatar_payload(asset: UserAvatar) -> dict:
    return {
        "id": asset.id,
        "avatar_id": asset.heygen_avatar_id,
        "asset_id": asset.id,
        "name": asset.name,
        "source": "photo",
        "avatar_type": asset.avatar_type,
        "preview_image_url": asset.preview_image_url or asset.source_image_url,
        "preview_video_url": asset.preview_video_url,
        "source_image_url": asset.source_image_url,
        "status": asset.status,
        "enabled": bool(asset.enabled),
        "created_at": to_utc_iso(asset.created_at),
        "updated_at": to_utc_iso(asset.updated_at),
    }


def user_avatar_task_payload(task: UserAvatarTask, asset: UserAvatar | None = None) -> dict:
    preview_image_url = asset.preview_image_url if asset and asset.preview_image_url else task.source_image_url
    return {
        "id": task.id,
        "name": task.name,
        "avatar_type": task.avatar_type,
        "status": task.status,
        "progress": provider_avatar_progress(task.status),
        "error_message": task.error_message,
        "source_image_url": task.source_image_url,
        "preview_image_url": preview_image_url,
        "preview_video_url": asset.preview_video_url if asset else "",
        "provider": task.provider,
        "provider_task_id": task.provider_task_id,
        "provider_avatar_id": task.provider_avatar_id,
        "avatar_id": asset.heygen_avatar_id if asset else (task.provider_avatar_id or ""),
        "result_avatar_id": task.result_avatar_id,
        "credit_cost": int(task.credit_cost or 0),
        "credit_refunded": bool(task.credit_refunded),
        "created_at": to_utc_iso(task.created_at),
        "updated_at": to_utc_iso(task.updated_at),
    }


async def resolve_avatar(db: AsyncSession, *, avatar_id: str, user_id: int) -> ResolvedAvatar | None:
    result = await db.execute(
        select(UserAvatar).where(
            UserAvatar.user_id == user_id,
            UserAvatar.heygen_avatar_id == avatar_id,
            UserAvatar.enabled == True,  # noqa: E712
            UserAvatar.status == "active",
            UserAvatar.archived_at.is_(None),
        )
    )
    user_avatar = result.scalar_one_or_none()
    if user_avatar:
        return ResolvedAvatar(
            avatar_id=user_avatar.heygen_avatar_id,
            name=user_avatar.name,
            preview_image_url=user_avatar.preview_image_url or user_avatar.source_image_url or "",
            preview_video_url=user_avatar.preview_video_url or "",
            source="photo",
            asset_id=user_avatar.id,
            avatar_type=user_avatar.avatar_type,
        )
    result = await db.execute(
        select(HeygenAvatar).where(
            HeygenAvatar.avatar_id == avatar_id,
            HeygenAvatar.enabled == True,  # noqa: E712
        )
    )
    avatar = result.scalar_one_or_none()
    if not avatar:
        return None
    return ResolvedAvatar(
        avatar_id=avatar.avatar_id,
        name=avatar.name,
        preview_image_url=avatar.preview_image_url or "",
        preview_video_url=avatar.preview_video_url or "",
        source="system",
        asset_id=avatar.id,
        avatar_type=avatar.avatar_type,
    )


async def get_photo_avatar_asset(
    db: AsyncSession,
    *,
    asset_id: str,
    user_id: int,
) -> UserAvatar | None:
    result = await db.execute(
        select(UserAvatar).where(
            UserAvatar.id == asset_id,
            UserAvatar.user_id == user_id,
            UserAvatar.enabled == True,  # noqa: E712
            UserAvatar.status == "active",
            UserAvatar.archived_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_enabled_voice(db: AsyncSession, voice_id: str) -> HeygenVoice | None:
    result = await db.execute(
        select(HeygenVoice).where(HeygenVoice.voice_id == voice_id, HeygenVoice.enabled == True)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def get_available_audio_asset(
    db: AsyncSession,
    *,
    audio_asset_id: str,
    user_id: int,
) -> UserAudioAsset | None:
    result = await db.execute(
        select(UserAudioAsset).where(
            UserAudioAsset.id == audio_asset_id,
            UserAudioAsset.user_id == user_id,
            UserAudioAsset.enabled == True,  # noqa: E712
            UserAudioAsset.archived_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_user_avatar_task(db: AsyncSession, *, task_id: str, user_id: int) -> UserAvatarTask | None:
    result = await db.execute(
        select(UserAvatarTask).where(
            UserAvatarTask.id == task_id,
            UserAvatarTask.user_id == user_id,
            UserAvatarTask.archived_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_user_avatars_by_ids(db: AsyncSession, avatar_ids: list[str]) -> dict[str, UserAvatar]:
    ids = [item for item in avatar_ids if item]
    if not ids:
        return {}
    result = await db.execute(select(UserAvatar).where(UserAvatar.id.in_(ids)))
    return {item.id: item for item in result.scalars().all()}


async def refund_user_avatar_task_if_needed(
    db: AsyncSession,
    task: UserAvatarTask,
    *,
    note: str,
) -> int | None:
    if task.credit_refunded or int(task.credit_cost or 0) <= 0:
        return None
    credits = await refund_user_credits(db, task.user_id, int(task.credit_cost), note=note)
    task.credit_refunded = True
    return credits


def extract_provider_avatar_identity(data: dict) -> tuple[str, str]:
    look = data.get("avatar_item") if isinstance(data.get("avatar_item"), dict) else data.get("avatar")
    look = look if isinstance(look, dict) else {}
    avatar_look_id = clean_text(look.get("id") or data.get("avatar_look_id") or data.get("avatar_id"))
    return clean_text(data.get("avatar_group_id") or data.get("group_id")), avatar_look_id


def extract_provider_avatar_urls(data: dict) -> tuple[str, str]:
    image_url = clean_text(data.get("preview_image_url") or data.get("image_url") or data.get("thumbnail_url"))
    video_url = clean_text(data.get("preview_video_url") or data.get("video_url") or data.get("preview_url"))
    return image_url, video_url


def extract_provider_avatar_status(data: dict) -> str:
    for key in ("avatar_item", "avatar_group"):
        value = data.get(key)
        if isinstance(value, dict) and clean_text(value.get("status")):
            return clean_text(value.get("status"))
    return clean_text(data.get("status"))


def extract_provider_avatar_error_message(data: dict) -> str | None:
    candidates = []
    for key in ("avatar_item", "avatar_group"):
        value = data.get(key)
        error = value.get("error") if isinstance(value, dict) else None
        if isinstance(error, dict):
            candidates.append(error.get("message"))
    candidates.extend([data.get("error_message"), data.get("failure_reason"), data.get("message")])
    return next((clean_text(item) for item in candidates if clean_text(item)), None)


async def upsert_user_avatar_from_task(
    db: AsyncSession,
    *,
    task: UserAvatarTask,
    heygen_avatar_id: str,
    preview_image_url: str,
    preview_video_url: str,
) -> UserAvatar:
    asset = await db.get(UserAvatar, task.result_avatar_id) if task.result_avatar_id else None
    if not asset:
        result = await db.execute(
            select(UserAvatar).where(
                UserAvatar.user_id == task.user_id,
                UserAvatar.heygen_avatar_id == heygen_avatar_id,
            )
        )
        asset = result.scalar_one_or_none()
    if not asset:
        asset = UserAvatar(user_id=task.user_id)
        db.add(asset)
    asset.avatar_type = task.avatar_type
    asset.name = task.name
    asset.heygen_avatar_id = heygen_avatar_id
    asset.preview_image_url = preview_image_url or task.source_image_url
    asset.preview_video_url = preview_video_url or None
    asset.source_image_url = task.source_image_url
    asset.source_object_key = task.source_object_key
    asset.status = "active"
    asset.enabled = True
    asset.archived_at = None
    asset.updated_at = utc_now()
    return asset


async def sync_user_avatar_task_from_provider(db: AsyncSession, task: UserAvatarTask) -> UserAvatarTask:
    if not task.provider_avatar_id:
        task.status = "failed"
        task.error_message = "HeyGen 未返回照片数字人 ID"
        await refund_user_avatar_task_if_needed(db, task, note=f"照片数字人创建失败退回 · {task.id}")
    else:
        async with httpx.AsyncClient(timeout=60) as client:
            data = await get_avatar_look(client, avatar_look_id=task.provider_avatar_id)
        error_message = extract_provider_avatar_error_message(data)
        task.status = provider_avatar_status(
            extract_provider_avatar_status(data),
            failure_message=error_message,
        )
        task.error_message = error_message
        if task.status == "done":
            image_url, video_url = extract_provider_avatar_urls(data)
            asset = await upsert_user_avatar_from_task(
                db,
                task=task,
                heygen_avatar_id=clean_text(data.get("id") or task.provider_avatar_id),
                preview_image_url=image_url,
                preview_video_url=video_url,
            )
            await db.flush()
            task.result_avatar_id = asset.id
            task.error_message = None
        elif task.status == "failed":
            await refund_user_avatar_task_if_needed(db, task, note=f"照片数字人创建失败退回 · {task.id}")
    await db.commit()
    await db.refresh(task)
    return task
