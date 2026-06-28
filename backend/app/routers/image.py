import uuid

import httpx
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import normalize_image_resolution
from app.core.deps import get_current_user, get_db
from app.core.ai_generation import (
    DashScopeConfigError,
    analyze_product_image,
    generate_image_strategy,
    optimize_free_image_prompt,
)
from app.core.generation_prompt_builder import (
    build_ai_write_prompt,
    build_image_generate_prompt,
    build_strategy_template_prompt,
)
from app.core.json_utils import dump_json_or_none, parse_json_or_none
from app.core.oss import OssConfigError, upload_image_bytes
from app.core.product_catalog import get_all_catalog, get_catalog
from app.core.prompt_snapshot import (
    build_prompt_snapshot,
    dump_prompt_snapshot,
    parse_prompt_snapshot,
)
from app.core.system_settings import (
    get_effective_image_credit_cost,
    get_effective_image_credit_costs,
)
from app.core.task_state import (
    clear_task_state_fields,
    merge_task_state,
    set_task_progress,
    set_task_status,
)
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import (
    get_user_credits as _get_user_credits,
    insufficient_credits_message as _insufficient_credits_message,
    refund_user_credits as _refund_user_credits,
)
from app.models import GenerationJob, ImageTask, User
from app.schemas.response import Response, fail, success
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate

router = APIRouter(prefix="/image", tags=["生图"])

IMAGE_PROMPT_STRATEGIES = {
    "product_suite": {"use_template": True},
    "product_image": {"use_template": True},
    "outfit": {"use_template": True},
    "free_image": {"use_template": False},
}


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


class ImageLabelItem(BaseModel):
    url: str
    label: str = ""


class AnalyzeImageRequest(BaseModel):
    images: list[ImageLabelItem]
    platform: str = ""
    scenario: str | None = None
    type_id: str | None = None


class StrategyRequest(BaseModel):
    scenario: str
    images: list[ImageLabelItem]
    platform: str = ""
    language: str = "中文"
    product_input: str = ""
    module_ids: list[str] = Field(default_factory=list)
    structure: list[dict] = Field(default_factory=list)
    scene_description: str = ""
    selected_model_name: str = ""
    scene_ids: list[str] = Field(default_factory=list)


class FreeImageOptimizeRequest(BaseModel):
    prompt: str


async def _build_image_task_prompt(
    *,
    db: AsyncSession,
    job: GenerationJob | None,
    req: GenerateRequest,
) -> tuple[str, dict]:
    user_prompt = (req.user_prompt or "").strip()
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
        type_id=req.type_id,
        title=req.title,
        user_prompt=user_prompt,
    )
    return built_prompt.final_prompt, built_prompt.prompt_snapshot


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


@router.post("/upload", response_model=Response)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    try:
        content = await file.read()
        uploaded = await upload_image_bytes(
            user_id=current_user.id,
            content=content,
            content_type=file.content_type or "",
        )
    except (ValueError, OssConfigError) as e:
        return fail(str(e))
    except Exception:
        return fail("图片上传失败")
    finally:
        await file.close()

    return success(
        {
            "url": uploaded.url,
            "object_key": uploaded.object_key,
            "content_type": uploaded.content_type,
            "size": uploaded.size,
        }
    )


@router.post("/analyze", response_model=Response)
async def analyze_image(
    req: AnalyzeImageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        template_prompt = await build_ai_write_prompt(
            db,
            scenario=req.scenario or "product_suite",
            platform=req.platform,
            type_id=req.type_id,
        )
        content = await analyze_product_image(
            images=[item.model_dump() for item in req.images],
            platform=req.platform,
            prompt=template_prompt or None,
        )
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        return fail("图片分析失败")

    return success({"content": content})


@router.post("/strategy", response_model=Response)
async def image_strategy(
    req: StrategyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scenario = req.scenario.strip()
    if scenario not in {"product_image", "product_suite", "outfit"}:
        return fail("不支持的策略场景")

    try:
        template_prompt = await build_strategy_template_prompt(
            db,
            scenario=scenario,
            platform=req.platform,
        )
        catalog = await get_catalog(db, scenario=scenario)
        images = [item.model_dump() for item in req.images]
        strategy = await generate_image_strategy(
            scenario=scenario,
            catalog=catalog,
            images=images,
            platform=req.platform,
            language=req.language,
            product_input=req.product_input,
            module_ids=req.module_ids,
            structure=req.structure,
            scene_description=req.scene_description,
            selected_model_name=req.selected_model_name,
            scene_ids=req.scene_ids,
            template_prompt=template_prompt,
        )
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        messages = {
            "product_image": "详情页策略生成失败",
            "product_suite": "套图策略生成失败",
            "outfit": "穿搭策略生成失败",
        }
        return fail(messages[scenario])

    return success(strategy)


@router.get("/catalog", response_model=Response)
async def image_catalog(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return success(await get_all_catalog(db))


@router.post("/free-image/optimize", response_model=Response)
async def free_image_optimize(
    req: FreeImageOptimizeRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        content = await optimize_free_image_prompt(req.prompt)
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        return fail("提示词优化失败")

    return success({"prompt": content})


@router.get("/credit-costs", response_model=Response)
async def image_credit_costs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        costs = await get_effective_image_credit_costs(db)
    except ValueError as exc:
        return fail(str(exc))
    return success({"costs": costs})


@router.post("/generate", response_model=Response)
async def create_image_task(
    req: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        credit_cost = await get_effective_image_credit_cost(db, req.resolution)
    except ValueError as exc:
        return fail(str(exc))
    normalized_resolution = normalize_image_resolution(req.resolution)
    if current_user.credits < credit_cost:
        return fail(_insufficient_credits_message(credit_cost, current_user.credits))

    job: GenerationJob | None = None
    if req.job_id:
        job_result = await db.execute(
            select(GenerationJob).where(
                GenerationJob.id == req.job_id,
                GenerationJob.user_id == current_user.id,
            )
        )
        job = job_result.scalar_one_or_none()
        if not job:
            return fail("任务不存在")
        if job.scenario not in IMAGE_PROMPT_STRATEGIES:
            return fail("任务类型不匹配")

    task_id = str(uuid.uuid4())
    try:
        final_prompt, prompt_snapshot = await _build_image_task_prompt(
            db=db,
            job=job,
            req=req,
        )
    except ValueError as exc:
        return fail(str(exc))

    # 原子扣积分 + 建任务同一事务，避免并发超扣和一致性漂移
    remaining_credits, fail_response = await deduct_credits_or_fail(
        db,
        current_user.id,
        credit_cost,
    )
    if fail_response is not None:
        return fail_response

    task = ImageTask(
        id=task_id,
        user_id=current_user.id,
        prompt=final_prompt,
        size=f"{req.ratio}/{normalized_resolution}",
        status="pending",
        job_id=req.job_id,
        type_id=req.type_id,
        title=req.title,
        sort_order=req.sort_order,
        prompt_snapshot_json=dump_prompt_snapshot(prompt_snapshot),
        settings_snapshot_json=dump_json_or_none(req.settings_snapshot),
        credit_cost=credit_cost,
    )
    db.add(task)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("任务创建失败，请稍后重试")

    reference_image_urls = [url for url in (req.image_urls or []) if url]

    # 入队失败：标记任务 failed 并退回积分，避免用户被扣却没活
    async def mark_task_failed(_refunded_credits: int) -> None:
        await db.execute(
            update(ImageTask)
            .where(ImageTask.id == task_id)
            .values(status="failed", credit_refunded=True)
        )

    enqueue_fail = await enqueue_or_compensate(
        get_redis_pool=lambda: request.app.state.redis_pool,
        db=db,
        job_name="generate_image",
        job_args=(
            task_id,
            final_prompt,
            req.ratio,
            normalized_resolution,
            reference_image_urls,
        ),
        user_id=current_user.id,
        credit_cost=credit_cost,
        remaining_credits=remaining_credits,
        refund_credits=_refund_user_credits,
        mark_failed=mark_task_failed,
        failure_message="任务入队失败，请稍后重试",
        failure_data={"task_id": task_id},
    )
    if enqueue_fail is not None:
        return enqueue_fail

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

    return success(
        {
            "task_id": task_id,
            "credits": remaining_credits,
            "credit_cost": credit_cost,
        }
    )


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

    latest_credits = await _get_user_credits(db, current_user.id)

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

    # 猜测 content type
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
