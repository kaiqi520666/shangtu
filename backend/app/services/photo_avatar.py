import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.oss import OssConfigError, upload_image_bytes
from app.core.providers.heygen_provider import create_photo_avatar, parse_heygen_error_message
from app.core.user_credits import get_user_credits
from app.models import UserAvatarTask
from app.schemas.response import Response, fail, success
from app.services.digital_human_assets import (
    extract_provider_avatar_error_message,
    extract_provider_avatar_identity,
    extract_provider_avatar_status,
    extract_provider_avatar_urls,
    get_user_avatar_task,
    get_user_avatars_by_ids,
    provider_avatar_status,
    refund_user_avatar_task_if_needed,
    sync_user_avatar_task_from_provider,
    upsert_user_avatar_from_task,
    user_avatar_task_payload,
)


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
