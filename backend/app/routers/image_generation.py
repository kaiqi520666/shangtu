from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import normalize_image_resolution
from app.core.deps import get_current_user, get_db
from app.core.prompt_snapshot import (
    build_prompt_snapshot,
    dump_prompt_snapshot,
    parse_prompt_snapshot,
)
from app.core.system_settings import (
    get_effective_image_credit_cost,
)
from app.core.task_state import (
    clear_task_state_fields,
    set_task_progress,
    set_task_status,
)
from app.core.time import utc_now
from app.core.user_credits import (
    insufficient_credits_message as _insufficient_credits_message,
    refund_user_credits as _refund_user_credits,
)
from app.models import GenerationJob, ImageTask, User
from app.schemas.response import Response, fail, success
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate
from app.services.image_generation import (
    IMAGE_PROMPT_STRATEGIES,
    ImageGeneratePayload,
    create_image_generation_task,
)
from app.routers.image_catalog import router as image_catalog_router
from app.routers.image_strategy import router as image_strategy_router
from app.routers.image_tasks import router as image_tasks_router
from app.routers.image_uploads import router as image_uploads_router

router = APIRouter(prefix="/image", tags=["生图"])
router.include_router(image_catalog_router)
router.include_router(image_strategy_router)
router.include_router(image_tasks_router)
router.include_router(image_uploads_router)

class GenerateRequest(BaseModel):
    user_prompt: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    ratio: str = "1:1"
    resolution: str = "1K"
    settings_snapshot: dict | None = None
    job_id: str | None = None
    type_id: str | None = None
    title: str | None = None
    sort_order: int = 0


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


@router.post("/generate", response_model=Response)
async def create_image_task(
    req: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result, failure = await create_image_generation_task(
        db=db,
        current_user=current_user,
        payload=ImageGeneratePayload(
            user_prompt=req.user_prompt,
            image_urls=req.image_urls,
            ratio=req.ratio,
            resolution=req.resolution,
            settings_snapshot=req.settings_snapshot,
            job_id=req.job_id,
            type_id=req.type_id,
            title=req.title,
            sort_order=req.sort_order,
        ),
        get_redis_pool=lambda: request.app.state.redis_pool,
    )
    if failure is not None:
        return failure

    return success(
        {
            "task_id": result.task_id,
            "credits": result.credits,
            "credit_cost": result.credit_cost,
        }
    )


class RegenerateRequest(BaseModel):
    edit_instruction: str | None = None
    user_prompt: str | None = None


@router.post("/task/{task_id}/regenerate", response_model=Response)
async def regenerate_image_task(
    task_id: str,
    req: RegenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """基于已有图片重新生成。新建 ImageTask，旧任务保留为历史资产。"""
    edit_instruction = (req.edit_instruction or "").strip()
    requested_user_prompt = (req.user_prompt or "").strip()
    if not requested_user_prompt and not edit_instruction:
        return fail("请输入用户提示词")

    result = await db.execute(
        select(ImageTask).where(
            ImageTask.id == task_id,
            ImageTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return fail("图片不存在")
    if task.archived:
        return fail("图片已被删除")
    if task.replaced_by_task_id:
        return fail("该图片已有新的重生版本，请刷新后操作最新图片")
    if not task.result_url:
        return fail("该图片尚未生成完成，无法重新生成")

    # 解析原 size -> ratio/resolution
    parts = task.size.split("/") if task.size else ["1:1", "1K"]
    ratio = parts[0] if len(parts) > 0 else "1:1"
    resolution = parts[1] if len(parts) > 1 else "1K"
    try:
        credit_cost = await get_effective_image_credit_cost(db, resolution)
    except ValueError as exc:
        return fail(str(exc))
    normalized_resolution = normalize_image_resolution(resolution)
    if current_user.credits < credit_cost:
        return fail(_insufficient_credits_message(credit_cost, current_user.credits))

    # 保留旧 result_url 供前端继续展示
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
    )
    if fail_response is not None:
        return fail_response

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
        return fail("重新生成失败，请稍后重试")

    # 入队 worker
    # TODO: 后续用 generation_attempts 做严格幂等退款
    async def reset_regenerate_task_state(redis) -> None:
        await clear_task_state_fields(redis, "image", new_task_id, ("result", "error"))
        await set_task_status(redis, "image", new_task_id, "pending", ttl=7200)
        await set_task_progress(redis, "image", new_task_id, 0)

    # 入队失败：退积分 + 标记新任务 failed + 恢复旧任务在工作台可见
    async def mark_regenerate_failed(_refunded_credits: int) -> None:
        task.replaced_by_task_id = None
        new_task.status = "failed"
        new_task.error_message = "任务入队失败"
        new_task.credit_refunded = True
        new_task.archived = True
        new_task.archived_at = utc_now()

    enqueue_fail = await enqueue_or_compensate(
        get_redis_pool=lambda: request.app.state.redis_pool,
        db=db,
        job_name="generate_image",
        job_args=(
            new_task_id,
            new_prompt,
            ratio,
            normalized_resolution,
            [old_result_url],  # 使用当前已生成图作为参考图
        ),
        user_id=current_user.id,
        credit_cost=credit_cost,
        remaining_credits=remaining_credits,
        refund_credits=_refund_user_credits,
        mark_failed=mark_regenerate_failed,
        failure_message="任务入队失败，请稍后重试",
        failure_data={"task_id": new_task_id, "source_task_id": task_id},
        before_enqueue=reset_regenerate_task_state,
    )
    if enqueue_fail is not None:
        return enqueue_fail

    return success(
        {
            "task_id": new_task_id,
            "source_task_id": task_id,
            "credits": remaining_credits,
            "credit_cost": credit_cost,
        }
    )
