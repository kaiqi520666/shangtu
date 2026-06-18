from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.time import to_utc_iso
from app.models import GenerationJob, ImageTask, User, VideoTask
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/asset", tags=["资产库"])

SCENARIO_FILTER = {"product_suite", "product_image", "outfit", "free_image", "product_video"}
PAGE_SIZE_MAX = 50


async def _query_image_assets(
    db: AsyncSession,
    *,
    user_id: int,
    scenario: str | None,
) -> list[dict]:
    if scenario == "product_video":
        return []
    stmt = (
        select(ImageTask, GenerationJob)
        .outerjoin(GenerationJob, GenerationJob.id == ImageTask.job_id)
        .where(
            ImageTask.user_id == user_id,
            ImageTask.status == "done",
            ImageTask.archived == False,  # noqa: E712
        )
    )
    if scenario:
        stmt = stmt.where(ImageTask.job_id.isnot(None), GenerationJob.scenario == scenario)
    result = await db.execute(stmt)
    return [
        {
            "task_id": task.id,
            "media_type": "image",
            "result_url": task.result_url,
            "title": task.title or "",
            "type_id": task.type_id or "",
            "scenario": job.scenario if job else "",
            "job_title": job.title if job else "",
            "created_at": to_utc_iso(task.created_at),
            "_created_at": task.created_at,
        }
        for task, job in result.all()
    ]


async def _query_video_assets(
    db: AsyncSession,
    *,
    user_id: int,
    scenario: str | None,
) -> list[dict]:
    if scenario and scenario != "product_video":
        return []
    stmt = (
        select(VideoTask, GenerationJob)
        .outerjoin(GenerationJob, GenerationJob.id == VideoTask.job_id)
        .where(
            VideoTask.user_id == user_id,
            VideoTask.status == "done",
            VideoTask.archived == False,  # noqa: E712
        )
    )
    result = await db.execute(stmt)
    return [
        {
            "task_id": task.id,
            "media_type": "video",
            "result_url": task.result_url,
            "title": task.title or "",
            "type_id": task.type_id or "",
            "scenario": job.scenario if job else "product_video",
            "job_title": job.title if job else "",
            "created_at": to_utc_iso(task.created_at),
            "_created_at": task.created_at,
        }
        for task, job in result.all()
    ]


@router.get("/list", response_model=Response)
async def list_assets(
    scenario: str | None = Query(None, description="按场景筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=PAGE_SIZE_MAX),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if scenario:
        if scenario not in SCENARIO_FILTER:
            return fail(f"不支持的场景类型：{scenario}")

    image_items = await _query_image_assets(db, user_id=current_user.id, scenario=scenario)
    video_items = await _query_video_assets(db, user_id=current_user.id, scenario=scenario)
    all_items = [*image_items, *video_items]
    all_items.sort(key=lambda item: item["_created_at"], reverse=True)
    total = len(all_items)
    start = (page - 1) * page_size
    items = all_items[start:start + page_size]
    for item in items:
        item.pop("_created_at", None)

    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


class BatchDeleteRequest(BaseModel):
    task_ids: list[str]
    media_type: str | None = None


@router.delete("/batch", response_model=Response)
async def batch_delete_assets(
    req: BatchDeleteRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not req.task_ids:
        return fail("请选择要删除的资产")
    if len(req.task_ids) > 50:
        return fail("单次最多删除 50 个资产")

    deleted_ids: list[str] = []
    deleted_video_ids: list[str] = []
    if req.media_type in (None, "", "image"):
        stmt = (
            delete(ImageTask)
            .where(
                ImageTask.id.in_(req.task_ids),
                ImageTask.user_id == current_user.id,
                ImageTask.status == "done",
            )
            .returning(ImageTask.id)
        )
        result = await db.execute(stmt)
        deleted_ids.extend([row[0] for row in result.all()])
    if req.media_type in (None, "", "video"):
        stmt = (
            delete(VideoTask)
            .where(
                VideoTask.id.in_(req.task_ids),
                VideoTask.user_id == current_user.id,
                VideoTask.status == "done",
            )
            .returning(VideoTask.id)
        )
        result = await db.execute(stmt)
        deleted_video_ids.extend([row[0] for row in result.all()])
    await db.commit()

    # 清理 Redis 缓存 key（best effort）
    if deleted_ids or deleted_video_ids:
        try:
            redis = request.app.state.redis_pool
            keys_to_del = []
            for task_id in deleted_ids:
                keys_to_del.extend([
                    f"task:{task_id}:status",
                    f"task:{task_id}:result",
                    f"task:{task_id}:error",
                    f"task:{task_id}:progress",
                ])
            for task_id in deleted_video_ids:
                keys_to_del.extend([
                    f"video_task:{task_id}:status",
                    f"video_task:{task_id}:result",
                    f"video_task:{task_id}:error",
                    f"video_task:{task_id}:progress",
                ])
            if keys_to_del:
                await redis.delete(*keys_to_del)
        except Exception:
            pass  # Redis 清理失败不影响主流程

    all_deleted_ids = [*deleted_ids, *deleted_video_ids]
    return success({"deleted": len(all_deleted_ids), "deleted_ids": all_deleted_ids})
