import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.json_utils import dump_json, parse_json_or_none
from app.core.time import to_utc_iso, utc_now
from app.models import GenerationJob, ImageTask, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/generation", tags=["生成任务"])

SUPPORTED_SCENARIOS = {"product_suite", "product_image", "outfit", "free_image"}
SCENARIO_TITLE_PREFIX = {
    "product_suite": "商品套图",
    "product_image": "商品详情图",
    "outfit": "服饰穿搭",
    "free_image": "自由生图",
}

TERMINAL_DONE = "done"
TERMINAL_FAILED = {"failed", "timeout"}
PROCESSING_STATUSES = {"pending", "processing"}


def _compute_display_status(job_status: str, total: int, completed: int, failed: int) -> str:
    """根据子任务聚合统计推断展示状态。"""
    if total == 0:
        return "draft"
    # 还有进行中的子任务
    pending_or_processing = total - completed - failed
    if pending_or_processing > 0:
        return "generating"
    if completed == total:
        return "done"
    if failed == total:
        return "failed"
    if failed > 0 and completed > 0:
        return "partial_failed"
    return job_status


class CreateJobRequest(BaseModel):
    scenario: str


class UpdateJobRequest(BaseModel):
    title: str | None = None
    settings: dict[str, Any] | None = None
    source_images: list[Any] | None = None
    input_text: str | None = None
    structure: list[Any] | None = None


def _default_title(scenario: str) -> str:
    prefix = SCENARIO_TITLE_PREFIX.get(scenario, scenario)
    return f"{prefix}_{utc_now():%Y%m%d_%H%M%S}"


@router.post("/jobs", response_model=Response)
async def create_job(
    req: CreateJobRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.scenario not in SUPPORTED_SCENARIOS:
        return fail(f"暂不支持的场景：{req.scenario}")

    job = GenerationJob(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        scenario=req.scenario,
        title=_default_title(req.scenario),
        status="draft",
    )
    db.add(job)
    try:
        await db.commit()
        await db.refresh(job)
    except Exception:
        await db.rollback()
        return fail("任务创建失败，请稍后重试")

    return success(
        {
            "job_id": job.id,
            "scenario": job.scenario,
            "title": job.title,
            "status": job.status,
            "created_at": to_utc_iso(job.created_at),
        }
    )


@router.get("/jobs", response_model=Response)
async def list_jobs(
    scenario: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if scenario not in SUPPORTED_SCENARIOS:
        return fail(f"暂不支持的场景：{scenario}")

    result = await db.execute(
        select(GenerationJob)
        .where(
            GenerationJob.user_id == current_user.id,
            GenerationJob.scenario == scenario,
            GenerationJob.archived == False,  # noqa: E712
        )
        .order_by(GenerationJob.created_at.desc())
    )
    jobs = result.scalars().all()
    if not jobs:
        return success([])

    job_ids = [job.id for job in jobs]
    tasks_rows = await db.execute(
        select(ImageTask.job_id, ImageTask.status).where(
            ImageTask.user_id == current_user.id,
            ImageTask.job_id.in_(job_ids),
            ImageTask.archived == False,  # noqa: E712
            ImageTask.replaced_by_task_id.is_(None),
        )
    )
    stats: dict[str, dict[str, int]] = {
        jid: {"total": 0, "completed": 0, "failed": 0} for jid in job_ids
    }
    for job_id, status in tasks_rows.all():
        bucket = stats.get(job_id)
        if not bucket:
            continue
        bucket["total"] += 1
        if status == TERMINAL_DONE:
            bucket["completed"] += 1
        elif status in TERMINAL_FAILED:
            bucket["failed"] += 1

    items = [
        {
            "job_id": job.id,
            "scenario": job.scenario,
            "title": job.title,
            "status": job.status,
            "display_status": _compute_display_status(
                job.status,
                stats[job.id]["total"],
                stats[job.id]["completed"],
                stats[job.id]["failed"],
            ),
            "created_at": to_utc_iso(job.created_at),
            "updated_at": to_utc_iso(job.updated_at),
            "total": stats[job.id]["total"],
            "completed": stats[job.id]["completed"],
            "failed": stats[job.id]["failed"],
        }
        for job in jobs
    ]
    return success(items)


@router.get("/jobs/{job_id}", response_model=Response)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == current_user.id,
            GenerationJob.archived == False,  # noqa: E712
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        return fail("任务不存在")

    tasks_result = await db.execute(
        select(ImageTask)
        .where(
            ImageTask.job_id == job_id,
            ImageTask.user_id == current_user.id,
            ImageTask.archived == False,  # noqa: E712
            ImageTask.replaced_by_task_id.is_(None),
        )
        .order_by(ImageTask.sort_order.asc(), ImageTask.created_at.asc())
    )
    items = [
        {
            "task_id": task.id,
            "type_id": task.type_id,
            "title": task.title,
            "sort_order": task.sort_order,
            "status": task.status,
            "progress": task.progress or 0,
            "result_url": task.result_url,
            "size": task.size,
            "error_message": task.error_message,
            "credit_cost": task.credit_cost,
            "credit_refunded": bool(task.credit_refunded),
            "replaced_by_task_id": task.replaced_by_task_id,
            "prompt": task.prompt,
            "edit_instruction": task.edit_instruction,
            "system_prompt_snapshot": task.system_prompt_snapshot,
            "task_prompt_snapshot": task.task_prompt_snapshot,
            "user_prompt": task.user_prompt,
            "prompt_template_refs": parse_json_or_none(task.prompt_template_refs_json),
            "settings_snapshot": parse_json_or_none(task.settings_snapshot_json),
        }
        for task in tasks_result.scalars().all()
    ]

    total = len(items)
    completed = sum(1 for t in items if t["status"] == TERMINAL_DONE)
    failed = sum(1 for t in items if t["status"] in TERMINAL_FAILED)

    return success(
        {
            "job_id": job.id,
            "scenario": job.scenario,
            "title": job.title,
            "status": job.status,
            "display_status": _compute_display_status(
                job.status, total, completed, failed
            ),
            "settings": parse_json_or_none(job.settings_json),
            "source_images": parse_json_or_none(job.source_images_json),
            "input_text": job.input_text,
            "structure": parse_json_or_none(job.structure_json),
            "items": items,
            "created_at": to_utc_iso(job.created_at),
            "updated_at": to_utc_iso(job.updated_at),
        }
    )


@router.patch("/jobs/{job_id}", response_model=Response)
async def update_job(
    job_id: str,
    req: UpdateJobRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        return fail("任务不存在")

    if req.title is not None:
        title = req.title.strip()
        if not (1 <= len(title) <= 100):
            return fail("任务标题长度需在 1-100 字之间")
        job.title = title
    if req.settings is not None:
        job.settings_json = dump_json(req.settings)
    if req.source_images is not None:
        job.source_images_json = dump_json(req.source_images)
    if req.input_text is not None:
        job.input_text = req.input_text
    if req.structure is not None:
        job.structure_json = dump_json(req.structure)

    job.updated_at = utc_now()

    try:
        await db.commit()
        await db.refresh(job)
    except Exception:
        await db.rollback()
        return fail("任务更新失败，请稍后重试")

    return success(
        {
            "job_id": job.id,
            "scenario": job.scenario,
            "title": job.title,
            "status": job.status,
            "updated_at": to_utc_iso(job.updated_at),
        }
    )


@router.delete("/jobs/{job_id}", response_model=Response)
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        return fail("任务不存在")

    job.archived = True
    job.archived_at = utc_now()

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("删除失败，请稍后重试")

    return success({"job_id": job_id})
