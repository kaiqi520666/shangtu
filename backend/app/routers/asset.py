from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import delete, func, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.task_state import task_state_keys
from app.core.time import to_utc_iso
from app.models import GenerationJob, ImageTask, User, VideoTask
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/asset", tags=["资产库"])

SCENARIO_FILTER = {"product_suite", "product_image", "outfit", "free_image", "product_video"}
PAGE_SIZE_MAX = 50


def _image_asset_select(user_id: int, scenario: str | None):
    if scenario == "product_video":
        return None
    stmt = (
        select(
            ImageTask.id.label("task_id"),
            literal("image").label("media_type"),
            ImageTask.result_url.label("result_url"),
            ImageTask.title.label("title"),
            ImageTask.type_id.label("type_id"),
            func.coalesce(GenerationJob.scenario, literal("")).label("scenario"),
            func.coalesce(GenerationJob.title, literal("")).label("job_title"),
            ImageTask.created_at.label("created_at"),
        )
        .outerjoin(GenerationJob, GenerationJob.id == ImageTask.job_id)
        .where(
            ImageTask.user_id == user_id,
            ImageTask.status == "done",
            ImageTask.archived.is_(False),
        )
    )
    if scenario:
        stmt = stmt.where(ImageTask.job_id.isnot(None), GenerationJob.scenario == scenario)
    return stmt


def _video_asset_select(user_id: int, scenario: str | None):
    if scenario and scenario != "product_video":
        return None
    return (
        select(
            VideoTask.id.label("task_id"),
            literal("video").label("media_type"),
            VideoTask.result_url.label("result_url"),
            VideoTask.title.label("title"),
            VideoTask.type_id.label("type_id"),
            func.coalesce(GenerationJob.scenario, literal("product_video")).label("scenario"),
            func.coalesce(GenerationJob.title, literal("")).label("job_title"),
            VideoTask.created_at.label("created_at"),
        )
        .outerjoin(GenerationJob, GenerationJob.id == VideoTask.job_id)
        .where(
            VideoTask.user_id == user_id,
            VideoTask.status == "done",
            VideoTask.archived.is_(False),
        )
    )


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

    start = (page - 1) * page_size
    selects = [
        stmt
        for stmt in (
            _image_asset_select(current_user.id, scenario),
            _video_asset_select(current_user.id, scenario),
        )
        if stmt is not None
    ]
    if not selects:
        return success({
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
        })

    asset_rows = (union_all(*selects) if len(selects) > 1 else selects[0]).subquery()
    total = int((await db.execute(select(func.count()).select_from(asset_rows))).scalar_one() or 0)
    result = await db.execute(
        select(asset_rows)
        .order_by(asset_rows.c.created_at.desc())
        .offset(start)
        .limit(page_size)
    )
    items = [
        {
            "task_id": row["task_id"],
            "media_type": row["media_type"],
            "result_url": row["result_url"],
            "title": row["title"] or "",
            "type_id": row["type_id"] or "",
            "scenario": row["scenario"] or "",
            "job_title": row["job_title"] or "",
            "created_at": to_utc_iso(row["created_at"]),
        }
        for row in result.mappings().all()
    ]

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
                keys_to_del.extend(task_state_keys("image", task_id))
            for task_id in deleted_video_ids:
                keys_to_del.extend(task_state_keys("video", task_id))
            if keys_to_del:
                await redis.delete(*keys_to_del)
        except Exception:
            pass  # Redis 清理失败不影响主流程

    all_deleted_ids = [*deleted_ids, *deleted_video_ids]
    return success({"deleted": len(all_deleted_ids), "deleted_ids": all_deleted_ids})
