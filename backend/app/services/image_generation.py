import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import normalize_image_resolution
from app.core.generation_prompt_builder import build_image_generate_prompt
from app.core.json_utils import dump_json_or_none
from app.core.prompt_snapshot import build_prompt_snapshot, dump_prompt_snapshot
from app.core.system_settings import get_effective_image_credit_cost
from app.core.user_credits import (
    insufficient_credits_message,
    refund_user_credits,
)
from app.models import GenerationJob, ImageTask, User
from app.schemas.response import Response, fail
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate

IMAGE_PROMPT_STRATEGIES = {
    "product_suite": {"use_template": True},
    "product_image": {"use_template": True},
    "outfit": {"use_template": True},
    "free_image": {"use_template": False},
}


@dataclass(slots=True)
class ImageGeneratePayload:
    user_prompt: str | None
    image_urls: list[str]
    ratio: str
    resolution: str
    settings_snapshot: dict | None
    job_id: str | None
    type_id: str | None
    title: str | None
    sort_order: int


@dataclass(slots=True)
class ImageGenerateResult:
    task_id: str
    credits: int
    credit_cost: int


async def _build_image_task_prompt(
    *,
    db: AsyncSession,
    job: GenerationJob | None,
    payload: ImageGeneratePayload,
) -> tuple[str, dict]:
    user_prompt = (payload.user_prompt or "").strip()
    if job is None:
        if not user_prompt:
            raise ValueError("请输入提示词")
        return user_prompt, build_prompt_snapshot(user=user_prompt, final=user_prompt)

    strategy = IMAGE_PROMPT_STRATEGIES[job.scenario]
    if not strategy["use_template"]:
        if not user_prompt:
            raise ValueError("请输入提示词")
        return user_prompt, build_prompt_snapshot(user=user_prompt, final=user_prompt)

    built_prompt = await build_image_generate_prompt(
        db,
        job=job,
        type_id=payload.type_id,
        title=payload.title,
        user_prompt=user_prompt,
    )
    return built_prompt.final_prompt, built_prompt.prompt_snapshot


async def create_image_generation_task(
    *,
    db: AsyncSession,
    current_user: User,
    payload: ImageGeneratePayload,
    get_redis_pool: Callable[[], Any],
) -> tuple[ImageGenerateResult | None, Response | None]:
    try:
        credit_cost = await get_effective_image_credit_cost(db, payload.resolution)
    except ValueError as exc:
        return None, fail(str(exc))
    normalized_resolution = normalize_image_resolution(payload.resolution)
    if current_user.credits < credit_cost:
        return None, fail(insufficient_credits_message(credit_cost, current_user.credits))

    job: GenerationJob | None = None
    if payload.job_id:
        job_result = await db.execute(
            select(GenerationJob).where(
                GenerationJob.id == payload.job_id,
                GenerationJob.user_id == current_user.id,
            )
        )
        job = job_result.scalar_one_or_none()
        if not job:
            return None, fail("任务不存在")
        if job.scenario not in IMAGE_PROMPT_STRATEGIES:
            return None, fail("任务类型不匹配")

    task_id = str(uuid.uuid4())
    try:
        final_prompt, prompt_snapshot = await _build_image_task_prompt(
            db=db,
            job=job,
            payload=payload,
        )
    except ValueError as exc:
        return None, fail(str(exc))

    # 原子扣积分 + 建任务同一事务，避免并发超扣和一致性漂移
    remaining_credits, fail_response = await deduct_credits_or_fail(
        db,
        current_user.id,
        credit_cost,
    )
    if fail_response is not None:
        return None, fail_response

    task = ImageTask(
        id=task_id,
        user_id=current_user.id,
        prompt=final_prompt,
        size=f"{payload.ratio}/{normalized_resolution}",
        status="pending",
        job_id=payload.job_id,
        type_id=payload.type_id,
        title=payload.title,
        sort_order=payload.sort_order,
        prompt_snapshot_json=dump_prompt_snapshot(prompt_snapshot),
        settings_snapshot_json=dump_json_or_none(payload.settings_snapshot),
        credit_cost=credit_cost,
    )
    db.add(task)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return None, fail("任务创建失败，请稍后重试")

    reference_image_urls = [url for url in (payload.image_urls or []) if url]

    async def mark_task_failed(_refunded_credits: int) -> None:
        await db.execute(
            update(ImageTask)
            .where(ImageTask.id == task_id)
            .values(status="failed", credit_refunded=True)
        )

    enqueue_fail = await enqueue_or_compensate(
        get_redis_pool=get_redis_pool,
        db=db,
        job_name="generate_image",
        job_args=(
            task_id,
            final_prompt,
            payload.ratio,
            normalized_resolution,
            reference_image_urls,
        ),
        user_id=current_user.id,
        credit_cost=credit_cost,
        remaining_credits=remaining_credits,
        refund_credits=refund_user_credits,
        mark_failed=mark_task_failed,
        failure_message="任务入队失败，请稍后重试",
        failure_data={"task_id": task_id},
    )
    if enqueue_fail is not None:
        return None, enqueue_fail

    if job is not None and job.status != "generating":
        try:
            await db.execute(
                update(GenerationJob)
                .where(GenerationJob.id == job.id)
                .values(status="generating")
            )
            await db.commit()
        except Exception:
            await db.rollback()

    return (
        ImageGenerateResult(
            task_id=task_id,
            credits=remaining_credits,
            credit_cost=credit_cost,
        ),
        None,
    )
