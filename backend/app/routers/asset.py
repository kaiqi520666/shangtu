from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import GenerationJob, ImageTask, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/asset", tags=["资产库"])

SCENARIO_FILTER = {"product_suite", "product_image", "outfit"}
PAGE_SIZE_MAX = 50


@router.get("/list", response_model=Response)
async def list_assets(
    scenario: str | None = Query(None, description="按场景筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=PAGE_SIZE_MAX),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 基础条件：当前用户、已完成、未归档
    base_conditions = [
        ImageTask.user_id == current_user.id,
        ImageTask.status == "done",
        ImageTask.archived == False,  # noqa: E712
    ]

    if scenario:
        if scenario not in SCENARIO_FILTER:
            return fail(f"不支持的场景类型：{scenario}")
        # 通过 job_id 关联 generation_jobs 取 scenario
        base_conditions.append(ImageTask.job_id.isnot(None))
        base_conditions.append(GenerationJob.id == ImageTask.job_id)
        base_conditions.append(GenerationJob.scenario == scenario)
        count_query = (
            select(func.count())
            .select_from(ImageTask)
            .join(GenerationJob, GenerationJob.id == ImageTask.job_id)
            .where(*base_conditions[:3])  # user, status, archived
            .where(GenerationJob.scenario == scenario)
        )
        items_query = (
            select(
                ImageTask.id,
                ImageTask.result_url,
                ImageTask.title,
                ImageTask.type_id,
                ImageTask.job_id,
                ImageTask.created_at,
                GenerationJob.scenario,
                GenerationJob.title.label("job_title"),
            )
            .join(GenerationJob, GenerationJob.id == ImageTask.job_id)
            .where(*base_conditions[:3])
            .where(GenerationJob.scenario == scenario)
            .order_by(ImageTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    else:
        # 全部：含有 job_id 的用 left join 取 scenario，无 job_id 的也返回
        count_query = (
            select(func.count())
            .select_from(ImageTask)
            .where(*base_conditions)
        )
        items_query = (
            select(
                ImageTask.id,
                ImageTask.result_url,
                ImageTask.title,
                ImageTask.type_id,
                ImageTask.job_id,
                ImageTask.created_at,
                GenerationJob.scenario,
                GenerationJob.title.label("job_title"),
            )
            .outerjoin(GenerationJob, GenerationJob.id == ImageTask.job_id)
            .where(*base_conditions)
            .order_by(ImageTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(items_query)).all()

    items = [
        {
            "task_id": row.id,
            "result_url": row.result_url,
            "title": row.title or "",
            "type_id": row.type_id or "",
            "scenario": row.scenario or "",
            "job_title": row.job_title or "",
            "created_at": (row.created_at.isoformat() + "Z") if row.created_at else "",
        }
        for row in rows
    ]

    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


class BatchDeleteRequest(BaseModel):
    task_ids: list[str]


@router.delete("/batch", response_model=Response)
async def batch_delete_assets(
    req: BatchDeleteRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not req.task_ids:
        return fail("请选择要删除的图片")
    if len(req.task_ids) > 50:
        return fail("单次最多删除 50 张")

    # 硬删除：只删属于当前用户且 status=done 的
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
    deleted_ids = [row[0] for row in result.all()]
    await db.commit()

    # 清理 Redis 缓存 key（best effort）
    if deleted_ids:
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
            if keys_to_del:
                await redis.delete(*keys_to_del)
        except Exception:
            pass  # Redis 清理失败不影响主流程

    return success({"deleted": len(deleted_ids), "deleted_ids": deleted_ids})
