import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import normalize_image_resolution
from app.core.generation_prompt_builder import build_image_generate_prompt
from app.core.json_utils import dump_json_or_none, parse_json_or_none
from app.core.prompt_snapshot import (
    build_prompt_snapshot,
    dump_prompt_snapshot,
    parse_prompt_snapshot,
)
from app.core.system_settings import get_effective_image_credit_cost
from app.core.scenarios import SCENARIO_TITLE_PREFIX
from app.core.task_state import (
    clear_task_state_fields,
    set_task_progress,
    set_task_status,
)
from app.core.time import utc_now
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


@dataclass(slots=True)
class ImageRegeneratePayload:
    edit_instruction: str | None
    user_prompt: str | None


@dataclass(slots=True)
class ImageRegenerateResult:
    task_id: str
    source_task_id: str
    credits: int
    credit_cost: int


def _image_consume_note(
    *,
    job: GenerationJob | None,
    payload: ImageGeneratePayload,
    resolution: str,
    regenerate: bool = False,
) -> str:
    scenario = job.scenario if job else "free_image"
    scenario_label = SCENARIO_TITLE_PREFIX.get(scenario, "生图")
    title = (payload.title or "").strip()
    parts = [scenario_label]
    if title:
        parts.append(title)
    parts.append(resolution)
    if regenerate:
        parts.append("重生")
    return " · ".join(parts)


def _compose_prompt_from_snapshot(prompt_snapshot: dict, user_prompt: str) -> str:
    return "\n".join(
        part
        for part in [
            "【系统提示词】",
            prompt_snapshot["system"].strip(),
            "【任务提示词】",
            prompt_snapshot["task"].strip(),
            "【用户提示词】",
            user_prompt.strip(),
        ]
        if part
    )


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
        if job.scenario == "product_image":
            structure = parse_json_or_none(job.structure_json)
            if not isinstance(structure, list) or not structure:
                return None, fail("请先生成并确认详情图方案")

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
        note=_image_consume_note(
            job=job,
            payload=payload,
            resolution=normalized_resolution,
        ),
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
        refund_note=f"图片任务入队失败退回 · {task_id}",
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


async def regenerate_image_generation_task(
    *,
    db: AsyncSession,
    current_user: User,
    task_id: str,
    payload: ImageRegeneratePayload,
    get_redis_pool: Callable[[], Any],
) -> tuple[ImageRegenerateResult | None, Response | None]:
    edit_instruction = (payload.edit_instruction or "").strip()
    requested_user_prompt = (payload.user_prompt or "").strip()
    if not requested_user_prompt and not edit_instruction:
        return None, fail("请输入用户提示词")

    result = await db.execute(
        select(ImageTask).where(
            ImageTask.id == task_id,
            ImageTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return None, fail("图片不存在")
    if task.archived:
        return None, fail("图片已被删除")
    if task.replaced_by_task_id:
        return None, fail("该图片已有新的重生版本，请刷新后操作最新图片")
    if not task.result_url:
        return None, fail("该图片尚未生成完成，无法重新生成")

    parts = task.size.split("/") if task.size else ["1:1", "1K"]
    ratio = parts[0] if len(parts) > 0 else "1:1"
    resolution = parts[1] if len(parts) > 1 else "1K"
    try:
        credit_cost = await get_effective_image_credit_cost(db, resolution)
    except ValueError as exc:
        return None, fail(str(exc))
    normalized_resolution = normalize_image_resolution(resolution)
    if current_user.credits < credit_cost:
        return None, fail(insufficient_credits_message(credit_cost, current_user.credits))

    old_result_url = task.result_url
    prompt_snapshot = parse_prompt_snapshot(task.prompt_snapshot_json)
    if task.job_id:
        job_result = await db.execute(
            select(GenerationJob).where(
                GenerationJob.id == task.job_id,
                GenerationJob.user_id == current_user.id,
            )
        )
        source_job = job_result.scalar_one_or_none()
    else:
        source_job = None

    if source_job and not IMAGE_PROMPT_STRATEGIES[source_job.scenario]["use_template"]:
        new_user_prompt = requested_user_prompt or edit_instruction
        new_prompt = new_user_prompt
        next_prompt_snapshot = build_prompt_snapshot(user=new_user_prompt, final=new_prompt)
    else:
        base_user_prompt = prompt_snapshot["user"]
        new_user_prompt = requested_user_prompt or (
            f"{base_user_prompt}\n\n【用户修改要求】{edit_instruction}"
            if base_user_prompt
            else edit_instruction
        )
        next_prompt_snapshot = build_prompt_snapshot(
            system=prompt_snapshot["system"],
            task=prompt_snapshot["task"],
            user=new_user_prompt,
            final="",
            template_refs=prompt_snapshot["template_refs"],
        )
        new_prompt = _compose_prompt_from_snapshot(next_prompt_snapshot, new_user_prompt)
        next_prompt_snapshot["final"] = new_prompt

    new_task_id = str(uuid.uuid4())

    # 原子扣积分 + 新建重生任务 + 标记旧任务被替换，放在同一事务
    remaining_credits, fail_response = await deduct_credits_or_fail(
        db,
        current_user.id,
        credit_cost,
        note=_image_consume_note(
            job=source_job,
            payload=ImageGeneratePayload(
                user_prompt=requested_user_prompt,
                image_urls=[old_result_url],
                ratio=ratio,
                resolution=normalized_resolution,
                settings_snapshot=None,
                job_id=task.job_id,
                type_id=task.type_id,
                title=task.title,
                sort_order=task.sort_order,
            ),
            resolution=normalized_resolution,
            regenerate=True,
        ),
    )
    if fail_response is not None:
        return None, fail_response

    new_task = ImageTask(
        id=new_task_id,
        user_id=current_user.id,
        job_id=task.job_id,
        type_id=task.type_id,
        title=task.title,
        sort_order=task.sort_order,
        prompt=new_prompt,
        size=f"{ratio}/{normalized_resolution}",
        status="pending",
        prompt_snapshot_json=dump_prompt_snapshot(next_prompt_snapshot),
        settings_snapshot_json=task.settings_snapshot_json,
        credit_cost=credit_cost,
        credit_refunded=False,
    )
    task.replaced_by_task_id = new_task_id
    db.add(new_task)

    try:
        await db.commit()
        await db.refresh(new_task)
    except Exception:
        await db.rollback()
        return None, fail("重新生成失败，请稍后重试")

    async def reset_regenerate_task_state(redis) -> None:
        await clear_task_state_fields(redis, "image", new_task_id, ("result", "error"))
        await set_task_status(redis, "image", new_task_id, "pending", ttl=7200)
        await set_task_progress(redis, "image", new_task_id, 0)

    async def mark_regenerate_failed(_refunded_credits: int) -> None:
        task.replaced_by_task_id = None
        new_task.status = "failed"
        new_task.error_message = "任务入队失败"
        new_task.credit_refunded = True
        new_task.archived = True
        new_task.archived_at = utc_now()

    enqueue_fail = await enqueue_or_compensate(
        get_redis_pool=get_redis_pool,
        db=db,
        job_name="generate_image",
        job_args=(
            new_task_id,
            new_prompt,
            ratio,
            normalized_resolution,
            [old_result_url],
        ),
        user_id=current_user.id,
        credit_cost=credit_cost,
        remaining_credits=remaining_credits,
        refund_credits=refund_user_credits,
        mark_failed=mark_regenerate_failed,
        failure_message="任务入队失败，请稍后重试",
        failure_data={"task_id": new_task_id, "source_task_id": task_id},
        refund_note=f"图片重生入队失败退回 · {new_task_id}",
        before_enqueue=reset_regenerate_task_state,
    )
    if enqueue_fail is not None:
        return None, enqueue_fail

    return (
        ImageRegenerateResult(
            task_id=new_task_id,
            source_task_id=task_id,
            credits=remaining_credits,
            credit_cost=credit_cost,
        ),
        None,
    )
