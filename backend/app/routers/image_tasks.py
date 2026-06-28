import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.json_utils import parse_json_or_none
from app.core.prompt_snapshot import parse_prompt_snapshot
from app.core.task_state import merge_task_state
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import get_user_credits
from app.models import ImageTask, User
from app.schemas.response import Response, fail, success

router = APIRouter()


@router.get("/task/{task_id}", response_model=Response)
async def get_image_task(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ImageTask).where(
            ImageTask.id == task_id,
            ImageTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return fail("任务不存在")

    redis_pool = getattr(request.app.state, "redis_pool", None)
    state = await merge_task_state(
        redis_pool,
        "image",
        task_id,
        db_status=task.status,
        db_result_url=task.result_url,
        db_error_message=task.error_message,
        db_progress=task.progress,
    )

    latest_credits = await get_user_credits(db, current_user.id)

    return success(
        {
            "status": state.status,
            "result_url": state.result_url,
            "size": task.size,
            "prompt": task.prompt,
            "prompt_snapshot": parse_prompt_snapshot(task.prompt_snapshot_json),
            "settings_snapshot": parse_json_or_none(task.settings_snapshot_json),
            "created_at": to_utc_iso(task.created_at),
            "error_message": state.error_message,
            "progress": state.progress,
            "credit_cost": task.credit_cost,
            "credits": latest_credits,
        }
    )


@router.get("/task/{task_id}/download")
async def download_task_image(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """代理下载图片，绕过浏览器跨域限制。"""
    result = await db.execute(
        select(ImageTask).where(
            ImageTask.id == task_id,
            ImageTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task or not task.result_url:
        return fail("图片不存在或尚未生成完成")

    async def stream():
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream("GET", task.result_url) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk

    url_lower = task.result_url.lower()
    if url_lower.endswith(".jpg") or url_lower.endswith(".jpeg"):
        media_type = "image/jpeg"
        ext = "jpg"
    elif url_lower.endswith(".webp"):
        media_type = "image/webp"
        ext = "webp"
    else:
        media_type = "image/png"
        ext = "png"

    filename = f"{task_id}.{ext}"
    return StreamingResponse(
        stream(),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tasks", response_model=Response)
async def list_image_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ImageTask)
        .where(
            ImageTask.user_id == current_user.id,
            ImageTask.archived.is_(False),
            ImageTask.replaced_by_task_id.is_(None),
        )
        .order_by(ImageTask.created_at.desc())
    )
    return success(result.scalars().all())


@router.delete("/task/{task_id}", response_model=Response)
async def delete_image_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """软删除单张图片（仅标记 archived，不物理删除 OSS 文件）。"""
    result = await db.execute(
        select(ImageTask).where(
            ImageTask.id == task_id,
            ImageTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return fail("图片不存在")

    task.archived = True
    task.archived_at = utc_now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("删除失败，请稍后重试")

    return success({"task_id": task_id})
