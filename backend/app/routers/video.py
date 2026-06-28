import uuid

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import normalize_video_resolution
from app.core.deps import get_current_user, get_db
from app.core.scenarios import VIDEO_SCENARIOS
from app.core.strategy.dashscope_client import (
    DashScopeConfigError,
    optimize_free_video_prompt,
)
from app.core.json_utils import dump_json_or_none, parse_json_or_none
from app.core.prompt_template_builder import build_strategy_template_prompt
from app.core.prompt_snapshot import dump_prompt_snapshot, parse_prompt_snapshot
from app.core.system_settings import (
    get_effective_video_credit_cost,
    get_effective_video_credit_costs,
)
from app.core.task_state import merge_task_state
from app.core.task_timeout import project_task_runtime_state
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import (
    get_user_credits,
    insufficient_credits_message,
    refund_user_credits,
)
from app.core.video_prompt_builder import build_video_generate_prompt
from app.core.video_strategy_generation import generate_video_strategy
from app.models import GenerationJob, User, VideoTask
from app.schemas.response import Response, fail, success
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate

router = APIRouter(prefix="/video", tags=["视频生成"])

VIDEO_INPUT_MODES = {"text_to_video", "image_to_video", "reference_to_video"}
VIDEO_ASPECT_RATIOS = {"16:9", "9:16", "1:1", "4:3", "3:4"}


class VideoGenerateRequest(BaseModel):
    scenario: str = "product_video"
    type_id: str
    title: str | None = None
    input_mode: str
    image_urls: list[str] = Field(default_factory=list)
    user_prompt: str | None = None
    duration: int = 6
    resolution: str = "720p"
    aspect_ratio: str = "9:16"
    settings_snapshot: dict | None = None
    sort_order: int = 0
    job_id: str | None = None


class VideoImageItem(BaseModel):
    url: str
    label: str = ""


class VideoStrategyRequest(BaseModel):
    type_id: str
    name: str | None = None
    input_mode: str
    images: list[VideoImageItem] = Field(default_factory=list)
    market: str = ""
    language: str = ""
    duration: int = 6
    aspect_ratio: str = "9:16"
    product_input: str = ""


class FreeVideoOptimizeRequest(BaseModel):
    prompt: str


def _clean_image_urls(image_urls: list[str]) -> list[str]:
    return [str(url).strip() for url in image_urls if str(url).strip()]


def _validate_video_inputs(input_mode: str, image_urls: list[str], *, allow_text: bool) -> str | None:
    if input_mode not in VIDEO_INPUT_MODES:
        return "不支持的视频素材模式"
    if input_mode == "text_to_video":
        return None if allow_text else "商品视频暂不支持文生视频模式"
    count = len(image_urls)
    if input_mode == "image_to_video" and count != 1:
        return "图生视频必须上传 1 张图片"
    if input_mode == "reference_to_video" and not 1 <= count <= 9:
        return "参考图生视频必须上传 1-9 张图片"
    return None


def _validate_aspect_ratio(aspect_ratio: str) -> str | None:
    if aspect_ratio not in VIDEO_ASPECT_RATIOS:
        supported = " / ".join(sorted(VIDEO_ASPECT_RATIOS))
        return f"不支持的视频比例：{aspect_ratio}，请选择 {supported}"
    return None


def _video_action(input_mode: str) -> str:
    if input_mode == "text_to_video":
        return "text-to-video"
    if input_mode == "image_to_video":
        return "image-to-video"
    return "reference-to-video"


def _normalize_video_scenario(raw: str | None) -> str:
    return (raw or "product_video").strip() or "product_video"


@router.get("/credit-costs", response_model=Response)
async def video_credit_costs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        costs = await get_effective_video_credit_costs(db)
    except ValueError as exc:
        return fail(str(exc))
    return success({"costs": costs})


@router.post("/strategy", response_model=Response)
async def video_strategy(
    req: VideoStrategyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    images = [item.model_dump() for item in req.images]
    image_urls = _clean_image_urls([item["url"] for item in images])
    input_error = _validate_video_inputs(req.input_mode, image_urls, allow_text=False)
    if input_error:
        return fail(input_error)

    aspect_ratio = str(req.aspect_ratio or "").strip()
    aspect_error = _validate_aspect_ratio(aspect_ratio)
    if aspect_error:
        return fail(aspect_error)

    try:
        template_prompt = await build_strategy_template_prompt(
            db,
            scenario="product_video",
            platform=req.market,
            type_id=req.type_id,
        )
        strategy = await generate_video_strategy(
            type_id=req.type_id,
            name=req.name or req.type_id,
            input_mode=req.input_mode,
            market=req.market,
            language=req.language,
            duration=req.duration,
            aspect_ratio=aspect_ratio,
            product_input=req.product_input,
            images=images,
            template_prompt=template_prompt,
        )
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        return fail("视频提示词生成失败")

    return success(strategy)


@router.post("/free-video/optimize", response_model=Response)
async def free_video_optimize(
    req: FreeVideoOptimizeRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        content = await optimize_free_video_prompt(req.prompt)
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        return fail("视频提示词优化失败")

    return success({"prompt": content})


@router.post("/generate", response_model=Response)
async def create_video_task(
    req: VideoGenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scenario = _normalize_video_scenario(req.scenario)
    if scenario not in VIDEO_SCENARIOS:
        return fail("不支持的视频场景")

    image_urls = _clean_image_urls(req.image_urls)
    input_error = _validate_video_inputs(
        req.input_mode,
        image_urls,
        allow_text=scenario == "free_video",
    )
    if input_error:
        return fail(input_error)

    aspect_ratio = str(req.aspect_ratio or "").strip()
    aspect_error = _validate_aspect_ratio(aspect_ratio)
    if aspect_error:
        return fail(aspect_error)

    try:
        normalized_resolution = normalize_video_resolution(req.resolution)
        credit_cost = await get_effective_video_credit_cost(
            db,
            normalized_resolution,
            req.duration,
        )
    except ValueError as exc:
        return fail(str(exc))

    if current_user.credits < credit_cost:
        return fail(insufficient_credits_message(credit_cost, current_user.credits))

    job: GenerationJob | None = None
    if req.job_id:
        job_result = await db.execute(
            select(GenerationJob).where(
                GenerationJob.id == req.job_id,
                GenerationJob.user_id == current_user.id,
                GenerationJob.scenario == scenario,
            )
        )
        job = job_result.scalar_one_or_none()
        if not job:
            return fail("任务不存在")

    settings_snapshot = {
        **(req.settings_snapshot or {}),
        "scenario": scenario,
        "type_id": req.type_id,
        "title": req.title,
        "input_mode": req.input_mode,
        "duration": req.duration,
        "resolution": normalized_resolution,
        "aspect_ratio": aspect_ratio,
    }

    try:
        built_prompt = await build_video_generate_prompt(
            db,
            type_id=req.type_id,
            title=req.title,
            user_prompt=req.user_prompt,
            settings=settings_snapshot,
        )
    except ValueError as exc:
        return fail(str(exc))

    remaining_credits, fail_response = await deduct_credits_or_fail(
        db,
        current_user.id,
        credit_cost,
    )
    if fail_response is not None:
        return fail_response

    task_id = str(uuid.uuid4())
    task = VideoTask(
        id=task_id,
        user_id=current_user.id,
        job_id=job.id if job else None,
        scenario=scenario,
        type_id=req.type_id,
        title=req.title,
        sort_order=req.sort_order,
        prompt=built_prompt.final_prompt,
        input_mode=req.input_mode,
        input_images_json=dump_json_or_none(image_urls),
        duration=req.duration,
        resolution=normalized_resolution,
        aspect_ratio=aspect_ratio,
        status="pending",
        prompt_snapshot_json=dump_prompt_snapshot(built_prompt.prompt_snapshot),
        settings_snapshot_json=dump_json_or_none(settings_snapshot),
        credit_cost=credit_cost,
    )
    db.add(task)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("视频任务创建失败，请稍后重试")

    async def mark_video_task_failed(_refunded_credits: int) -> None:
        await db.execute(
            update(VideoTask)
            .where(VideoTask.id == task_id)
            .values(status="failed", credit_refunded=True)
        )

    enqueue_fail = await enqueue_or_compensate(
        get_redis_pool=lambda: request.app.state.redis_pool,
        db=db,
        job_name="generate_video",
        job_args=(
            task_id,
            built_prompt.final_prompt,
            req.duration,
            aspect_ratio,
            normalized_resolution,
            _video_action(req.input_mode),
            image_urls,
        ),
        user_id=current_user.id,
        credit_cost=credit_cost,
        remaining_credits=remaining_credits,
        refund_credits=refund_user_credits,
        mark_failed=mark_video_task_failed,
        failure_message="视频任务入队失败，请稍后重试",
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
async def get_video_task(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == task_id,
            VideoTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return fail("视频任务不存在")

    redis_pool = getattr(request.app.state, "redis_pool", None)
    state = await merge_task_state(
        redis_pool,
        "video",
        task_id,
        db_status=task.status,
        db_result_url=task.result_url,
        db_error_message=task.error_message,
        db_progress=task.progress,
    )
    runtime = project_task_runtime_state(
        "video",
        status=state.status,
        error_message=state.error_message,
        progress=state.progress,
        result_url=state.result_url,
        created_at=task.created_at,
    )

    latest_credits = await get_user_credits(db, current_user.id)

    return success(
        {
            "task_id": task.id,
            "scenario": task.scenario,
            "status": runtime.status,
            "result_url": runtime.result_url,
            "prompt": task.prompt,
            "prompt_snapshot": parse_prompt_snapshot(task.prompt_snapshot_json),
            "settings_snapshot": parse_json_or_none(task.settings_snapshot_json),
            "input_mode": task.input_mode,
            "input_images": parse_json_or_none(task.input_images_json) or [],
            "duration": task.duration,
            "resolution": task.resolution,
            "aspect_ratio": task.aspect_ratio,
            "created_at": to_utc_iso(task.created_at),
            "error_message": runtime.error_message,
            "progress": runtime.progress,
            "credit_cost": task.credit_cost,
            "credits": latest_credits,
        }
    )


@router.delete("/task/{task_id}", response_model=Response)
async def delete_video_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """软删除单个视频任务（仅标记 archived，不物理删除 OSS 文件）。"""
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == task_id,
            VideoTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return fail("视频不存在")

    task.archived = True
    task.archived_at = utc_now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("删除失败，请稍后重试")

    return success({"task_id": task_id})


@router.get("/task/{task_id}/download")
async def download_video_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == task_id,
            VideoTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task or not task.result_url:
        return fail("视频不存在或尚未生成完成")

    async def stream():
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("GET", task.result_url) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk

    url_lower = task.result_url.lower()
    if url_lower.endswith(".webm"):
        media_type = "video/webm"
        ext = "webm"
    elif url_lower.endswith(".mov"):
        media_type = "video/quicktime"
        ext = "mov"
    else:
        media_type = "video/mp4"
        ext = "mp4"

    return StreamingResponse(
        stream(),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{task_id}.{ext}"'},
    )
