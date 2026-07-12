import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.oss import OssConfigError, upload_image_bytes
from app.core.providers.heygen_provider import (
    create_photo_avatar,
    get_avatar_look,
    parse_heygen_error_message,
)
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import get_user_credits, refund_user_credits
from app.models import UserAvatar, UserAvatarTask
from app.schemas.response import Response, fail, success
from app.services.heygen_task_lifecycle import clean_text


def provider_avatar_status(
    provider_status: str | None,
    *,
    failure_message: str | None = None,
) -> str:
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


def user_avatar_task_payload(
    task: UserAvatarTask,
    asset: UserAvatar | None = None,
) -> dict:
    preview_image_url = (
        asset.preview_image_url
        if asset and asset.preview_image_url
        else task.source_image_url
    )
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


async def get_user_avatar_task(
    db: AsyncSession,
    *,
    task_id: str,
    user_id: int,
) -> UserAvatarTask | None:
    result = await db.execute(
        select(UserAvatarTask).where(
            UserAvatarTask.id == task_id,
            UserAvatarTask.user_id == user_id,
            UserAvatarTask.archived_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_user_avatars_by_ids(
    db: AsyncSession,
    avatar_ids: list[str],
) -> dict[str, UserAvatar]:
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
    credits = await refund_user_credits(
        db,
        task.user_id,
        int(task.credit_cost),
        note=note,
    )
    task.credit_refunded = True
    return credits


def extract_provider_avatar_identity(data: dict) -> tuple[str, str]:
    look = (
        data.get("avatar_item")
        if isinstance(data.get("avatar_item"), dict)
        else data.get("avatar")
    )
    look = look if isinstance(look, dict) else {}
    avatar_look_id = clean_text(
        look.get("id") or data.get("avatar_look_id") or data.get("avatar_id")
    )
    return clean_text(data.get("avatar_group_id") or data.get("group_id")), avatar_look_id


def extract_provider_avatar_urls(data: dict) -> tuple[str, str]:
    image_url = clean_text(
        data.get("preview_image_url")
        or data.get("image_url")
        or data.get("thumbnail_url")
    )
    video_url = clean_text(
        data.get("preview_video_url")
        or data.get("video_url")
        or data.get("preview_url")
    )
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
    candidates.extend(
        [data.get("error_message"), data.get("failure_reason"), data.get("message")]
    )
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


async def sync_user_avatar_task_from_provider(
    db: AsyncSession,
    task: UserAvatarTask,
) -> UserAvatarTask:
    if not task.provider_avatar_id:
        task.status = "failed"
        task.error_message = "HeyGen 未返回照片数字人 ID"
        await refund_user_avatar_task_if_needed(
            db,
            task,
            note=f"照片数字人创建失败退回 · {task.id}",
        )
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
            await refund_user_avatar_task_if_needed(
                db,
                task,
                note=f"照片数字人创建失败退回 · {task.id}",
            )
    await db.commit()
    await db.refresh(task)
    return task


async def _fail_task(
    db: AsyncSession,
    task: UserAvatarTask,
    *,
    message: str,
) -> Response:
    task.status = "failed"
    task.error_message = message
    refunded = await refund_user_avatar_task_if_needed(
        db,
        task,
        note=f"照片数字人创建失败退回 · {task.id}",
    )
    await db.commit()
    credits = refunded if refunded is not None else await get_user_credits(db, task.user_id)
    return fail(
        message,
        data={"task_id": task.id, "credits": credits, "credit_cost": int(task.credit_cost or 0)},
    )


async def _apply_provider_result(
    db: AsyncSession,
    task: UserAvatarTask,
    provider_data: dict,
) -> None:
    provider_task_id, provider_avatar_id = extract_provider_avatar_identity(provider_data)
    if not provider_avatar_id:
        raise ValueError("HeyGen 未返回照片数字人 ID")
    task.provider_task_id = provider_task_id or provider_avatar_id
    task.provider_avatar_id = provider_avatar_id
    task.status = provider_avatar_status(extract_provider_avatar_status(provider_data))
    if task.status == "done":
        image_url, video_url = extract_provider_avatar_urls(provider_data)
        asset = await upsert_user_avatar_from_task(
            db,
            task=task,
            heygen_avatar_id=provider_avatar_id,
            preview_image_url=image_url,
            preview_video_url=video_url,
        )
        await db.flush()
        task.result_avatar_id = asset.id
    elif task.status == "failed":
        task.error_message = extract_provider_avatar_error_message(provider_data) or "HeyGen 创建失败，请稍后重试"
        await refund_user_avatar_task_if_needed(
            db,
            task,
            note=f"照片数字人创建失败退回 · {task.id}",
        )
    await db.commit()
    await db.refresh(task)


async def create_photo_avatar_task(
    *,
    db: AsyncSession,
    user_id: int,
    name: str,
    content: bytes,
    content_type: str,
) -> Response:
    try:
        uploaded = await upload_image_bytes(
            user_id=user_id,
            content=content,
            content_type=content_type,
            source="photo-avatars",
        )
    except (ValueError, OssConfigError) as exc:
        return fail(str(exc))
    except Exception:
        return fail("照片上传失败，请稍后重试")

    task = UserAvatarTask(
        user_id=user_id,
        avatar_type="photo",
        name=name,
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
                name=name,
                image_url=uploaded.url,
                idempotency_key=task.id,
            )
        await _apply_provider_result(db, task, provider_data)
    except ValueError as exc:
        return await _fail_task(db, task, message=str(exc))
    except httpx.HTTPError as exc:
        return await _fail_task(db, task, message=parse_heygen_error_message(exc))
    except Exception:
        return await _fail_task(db, task, message="HeyGen 创建失败，请稍后重试")

    assets = await get_user_avatars_by_ids(db, [task.result_avatar_id or ""])
    payload = user_avatar_task_payload(task, assets.get(task.result_avatar_id or ""))
    payload["credits"] = await get_user_credits(db, user_id)
    return success(payload)


async def poll_photo_avatar_task(
    *,
    db: AsyncSession,
    user_id: int,
    task_id: str,
) -> Response:
    task = await get_user_avatar_task(db, task_id=task_id, user_id=user_id)
    if not task:
        return fail("照片数字人任务不存在")
    if task.status in {"pending", "processing"} or (task.status == "done" and not task.result_avatar_id):
        try:
            task = await sync_user_avatar_task_from_provider(db, task)
        except ValueError as exc:
            await _fail_task(db, task, message=str(exc))
            await db.refresh(task)
        except httpx.HTTPError as exc:
            return fail(parse_heygen_error_message(exc))
        except Exception:
            return fail("HeyGen 状态查询失败，请稍后重试")
    assets = await get_user_avatars_by_ids(db, [task.result_avatar_id or ""])
    payload = user_avatar_task_payload(task, assets.get(task.result_avatar_id or ""))
    payload["credits"] = await get_user_credits(db, user_id)
    return success(payload)
