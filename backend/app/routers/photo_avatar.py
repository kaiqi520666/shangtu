import mimetypes

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.pagination import (
    PaginationParams,
    create_pagination_params,
    execute_pagination,
    page_payload,
)
from app.core.time import utc_now
from app.models import User, UserAvatar, UserAvatarTask
from app.schemas.response import Response, fail, success
from app.services.photo_avatar import (
    create_photo_avatar_task,
    get_photo_avatar_asset,
    get_user_avatar_task,
    get_user_avatars_by_ids,
    poll_photo_avatar_task as poll_task,
    user_avatar_payload,
    user_avatar_task_payload,
)
from app.services.heygen_task_lifecycle import clean_text

router = APIRouter()
PHOTO_AVATAR_PAGINATION = create_pagination_params(
    default_page_size=12,
    max_page_size=50,
)


@router.post("/photo-avatars/upload", response_model=Response)
async def upload_photo_avatar(
    file: UploadFile = File(...),
    name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    avatar_name = clean_text(name)[:120]
    if not avatar_name:
        return fail("请输入数字人名称")
    content_type = (file.content_type or "").strip()
    if not content_type and file.filename:
        content_type = mimetypes.guess_type(file.filename)[0] or ""
    try:
        content = await file.read()
    except Exception:
        return fail("照片上传失败，请稍后重试")
    finally:
        await file.close()
    return await create_photo_avatar_task(
        db=db,
        user_id=current_user.id,
        name=avatar_name,
        content=content,
        content_type=content_type,
    )


@router.get("/photo-avatars/tasks", response_model=Response)
async def list_photo_avatar_tasks(
    pagination: PaginationParams = Depends(PHOTO_AVATAR_PAGINATION),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [
        UserAvatarTask.user_id == current_user.id,
        UserAvatarTask.archived_at.is_(None),
        UserAvatarTask.avatar_type == "photo",
    ]
    total_stmt = select(func.count()).select_from(UserAvatarTask).where(*conditions)
    data_stmt = (
        select(UserAvatarTask)
        .where(*conditions)
        .order_by(UserAvatarTask.created_at.desc(), UserAvatarTask.id.desc())
    )
    total, result = await execute_pagination(
        db,
        count_statement=total_stmt,
        data_statement=data_stmt,
        pagination=pagination,
    )
    tasks = result.scalars().all()
    assets = await get_user_avatars_by_ids(db, [item.result_avatar_id or "" for item in tasks])
    items = [user_avatar_task_payload(item, assets.get(item.result_avatar_id or "")) for item in tasks]
    return success(page_payload(items, total, pagination.page, pagination.page_size))


@router.get("/photo-avatars/tasks/{task_id}/poll", response_model=Response)
async def poll_photo_avatar_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await poll_task(db=db, user_id=current_user.id, task_id=task_id)


@router.delete("/photo-avatars/tasks/{task_id}", response_model=Response)
async def delete_photo_avatar_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_user_avatar_task(db, task_id=task_id, user_id=current_user.id)
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
    pagination: PaginationParams = Depends(PHOTO_AVATAR_PAGINATION),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [
        UserAvatar.user_id == current_user.id,
        UserAvatar.avatar_type == "photo",
        UserAvatar.enabled.is_(True),
        UserAvatar.status == "active",
        UserAvatar.archived_at.is_(None),
    ]
    total_stmt = select(func.count()).select_from(UserAvatar).where(*conditions)
    data_stmt = (
        select(UserAvatar)
        .where(*conditions)
        .order_by(UserAvatar.created_at.desc(), UserAvatar.id.desc())
    )
    total, result = await execute_pagination(
        db,
        count_statement=total_stmt,
        data_statement=data_stmt,
        pagination=pagination,
    )
    return success(
        page_payload(
            [user_avatar_payload(item) for item in result.scalars().all()],
            total,
            pagination.page,
            pagination.page_size,
        )
    )


@router.delete("/photo-avatars/{asset_id}", response_model=Response)
async def delete_photo_avatar(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    asset = await get_photo_avatar_asset(db, asset_id=asset_id, user_id=current_user.id)
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
