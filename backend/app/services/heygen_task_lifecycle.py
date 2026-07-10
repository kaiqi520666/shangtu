from __future__ import annotations

import math
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import dump_json_or_none
from app.core.task_timeout import project_task_runtime_state
from app.core.time import utc_now
from app.core.user_credits import refund_user_credits
from app.models import GenerationJob, VideoTask


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_duration_seconds(value: float | int | None) -> int:
    try:
        return max(0, math.ceil(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def provider_task_status(
    provider_status: str | None,
    *,
    video_url: str | None = None,
    failure_message: str | None = None,
) -> str:
    normalized = clean_text(provider_status).lower()
    if video_url or normalized in {"completed", "done", "success", "succeeded"}:
        return "done"
    if normalized in {"failed", "error", "canceled", "cancelled"} or failure_message:
        return "failed"
    if normalized == "pending":
        return "pending"
    return "processing"


def task_progress(status: str) -> int:
    return {"done": 100, "failed": 0, "processing": 65}.get(status, 10)


async def get_or_create_video_job(
    db: AsyncSession,
    *,
    user_id: int,
    job_id: str | None,
    scenario: str,
    title: str,
    settings_snapshot: dict,
    input_text: str | None = None,
) -> GenerationJob | None:
    if job_id:
        result = await db.execute(
            select(GenerationJob).where(
                GenerationJob.id == job_id,
                GenerationJob.user_id == user_id,
                GenerationJob.scenario == scenario,
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            return None
        job.title = title
        job.settings_json = dump_json_or_none(settings_snapshot)
        job.input_text = input_text
        job.updated_at = utc_now()
        return job

    job = GenerationJob(
        id=str(uuid.uuid4()),
        user_id=user_id,
        scenario=scenario,
        title=title,
        status="draft",
        settings_json=dump_json_or_none(settings_snapshot),
        input_text=input_text,
    )
    db.add(job)
    return job


async def sync_video_job_status(
    db: AsyncSession,
    *,
    job_id: str | None,
    scenario: str,
) -> None:
    if not job_id:
        return
    job = await db.get(GenerationJob, job_id)
    if not job:
        return
    result = await db.execute(
        select(VideoTask.status, VideoTask.result_url, VideoTask.error_message, VideoTask.created_at).where(
            VideoTask.job_id == job_id,
            VideoTask.archived == False,  # noqa: E712
            VideoTask.scenario == scenario,
        )
    )
    rows = result.all()
    if not rows:
        job.status = "draft"
        job.updated_at = utc_now()
        return

    terminal = [
        project_task_runtime_state(
            "video",
            status=status,
            error_message=error_message,
            progress=0,
            result_url=result_url,
            created_at=created_at,
        ).status
        for status, result_url, error_message, created_at in rows
    ]
    if all(status == "done" for status in terminal):
        job.status = "done"
    elif all(status in {"failed", "timeout"} for status in terminal):
        job.status = "failed"
    else:
        job.status = "generating"
    job.updated_at = utc_now()


async def refund_video_task_if_needed(
    db: AsyncSession,
    task: VideoTask,
    *,
    note: str,
) -> int | None:
    if task.credit_refunded or int(task.credit_cost or 0) <= 0:
        return None
    credits = await refund_user_credits(db, task.user_id, int(task.credit_cost), note=note)
    task.credit_refunded = True
    return credits
