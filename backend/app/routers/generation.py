import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import GenerationJob, ImageTask, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/generation", tags=["生成任务"])

SUPPORTED_SCENARIOS = {"product_suite"}
SCENARIO_TITLE_PREFIX = {"product_suite": "商品套图"}

TERMINAL_DONE = "done"
TERMINAL_FAILED = {"failed", "timeout"}


class CreateJobRequest(BaseModel):
    scenario: str


def _parse_json(raw: str | None):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def _default_title(scenario: str) -> str:
    prefix = SCENARIO_TITLE_PREFIX.get(scenario, scenario)
    return f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}"


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
            "created_at": job.created_at,
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
            "created_at": job.created_at,
            "updated_at": job.updated_at,
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
            "error_message": task.error_message,
        }
        for task in tasks_result.scalars().all()
    ]

    return success(
        {
            "job_id": job.id,
            "scenario": job.scenario,
            "title": job.title,
            "status": job.status,
            "settings": _parse_json(job.settings_json),
            "source_images": _parse_json(job.source_images_json),
            "input_text": job.input_text,
            "structure": _parse_json(job.structure_json),
            "items": items,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
    )
