import json
import uuid

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import normalize_video_resolution
from app.core.deps import get_current_user, get_db
from app.core.image_analyzer import (
    DashScopeConfigError,
    generate_video_strategy,
)
from app.core.image_prompt_builder import (
    build_strategy_template_prompt,
    build_video_generate_prompt,
)
from app.core.json_utils import dump_json_or_none, parse_json_or_none
from app.core.prompt_snapshot import dump_prompt_snapshot, parse_prompt_snapshot
from app.core.system_settings import (
    get_effective_video_credit_cost,
    get_effective_video_credit_costs,
)
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import (
    deduct_user_credits,
    get_user_credits,
    insufficient_credits_message,
    refund_user_credits,
)
from app.models import GenerationJob, User, VideoTask
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/video", tags=["商品视频"])

VIDEO_INPUT_MODES = {"first_frame", "first_last_frame", "reference_images"}
VIDEO_ASPECT_RATIOS = {"16:9", "9:16", "1:1", "4:3", "3:4", "21:9"}


class VideoGenerateRequest(BaseModel):
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


def _redis_str(value) -> str | None:
    if value is None:
        return None
    return value.decode() if isinstance(value, bytes) else str(value)


def _parse_redis_result_url(value) -> str | None:
    raw = _redis_str(value)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    url = parsed.get("url")
    return url if isinstance(url, str) and url else None


def _clean_image_urls(image_urls: list[str]) -> list[str]:
    return [str(url).strip() for url in image_urls if str(url).strip()]


def _validate_video_inputs(input_mode: str, image_urls: list[str]) -> str | None:
    if input_mode not in VIDEO_INPUT_MODES:
        return "不支持的视频素材模式"
    count = len(image_urls)
    if input_mode == "first_frame" and count != 1:
        return "首帧生成必须上传 1 张图片"
    if input_mode == "first_last_frame" and count != 2:
        return "首尾帧过渡必须上传 2 张图片"
    if input_mode == "reference_images" and not 1 <= count <= 9:
        return "多参考生成必须上传 1-9 张图片"
    return None


def _validate_aspect_ratio(aspect_ratio: str) -> str | None:
    if aspect_ratio not in VIDEO_ASPECT_RATIOS:
        supported = " / ".join(sorted(VIDEO_ASPECT_RATIOS))
        return f"不支持的视频比例：{aspect_ratio}，请选择 {supported}"
    return None


def _build_image_with_roles(input_mode: str, image_urls: list[str]) -> list[dict[str, str]]:
    if input_mode == "first_frame":
        return [{"url": image_urls[0], "role": "first_frame"}]
    if input_mode == "first_last_frame":
        return [
            {"url": image_urls[0], "role": "first_frame"},
            {"url": image_urls[1], "role": "last_frame"},
        ]
    return [{"url": url, "role": "reference_image"} for url in image_urls]


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
    input_error = _validate_video_inputs(req.input_mode, image_urls)
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
        return fail("视频策略生成失败")

    return success(strategy)


@router.post("/generate", response_model=Response)
async def create_video_task(
    req: VideoGenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    image_urls = _clean_image_urls(req.image_urls)
    input_error = _validate_video_inputs(req.input_mode, image_urls)
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
                GenerationJob.scenario == "product_video",
            )
        )
        job = job_result.scalar_one_or_none()
        if not job:
            return fail("任务不存在")

    settings_snapshot = {
        **(req.settings_snapshot or {}),
        "scenario": "product_video",
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

    remaining_credits = await deduct_user_credits(db, current_user.id, credit_cost)
    if remaining_credits is None:
        await db.rollback()
        latest_credits = await get_user_credits(db, current_user.id)
        return fail(insufficient_credits_message(credit_cost, latest_credits))

    task_id = str(uuid.uuid4())
    task = VideoTask(
        id=task_id,
        user_id=current_user.id,
        job_id=job.id if job else None,
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

    image_with_roles = _build_image_with_roles(req.input_mode, image_urls)
    try:
        await request.app.state.redis_pool.enqueue_job(
            "generate_video",
            task_id,
            built_prompt.final_prompt,
            req.duration,
            aspect_ratio,
            normalized_resolution,
            image_with_roles,
        )
    except Exception:
        try:
            refunded_credits = await refund_user_credits(
                db, current_user.id, credit_cost
            )
            await db.execute(
                update(VideoTask)
                .where(VideoTask.id == task_id)
                .values(status="failed", credit_refunded=True)
            )
            await db.commit()
        except Exception:
            await db.rollback()
            refunded_credits = remaining_credits
        return fail(
            "视频任务入队失败，请稍后重试",
            data={
                "task_id": task_id,
                "credits": refunded_credits,
                "credit_cost": credit_cost,
            },
        )

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

    status = task.status
    result_url = task.result_url
    error_message: str | None = task.error_message
    progress: int = task.progress or 0

    redis_pool = getattr(request.app.state, "redis_pool", None)
    if redis_pool is not None:
        try:
            async with redis_pool.pipeline() as pipe:
                pipe.get(f"video_task:{task_id}:status")
                pipe.get(f"video_task:{task_id}:error")
                pipe.get(f"video_task:{task_id}:progress")
                pipe.get(f"video_task:{task_id}:result")
                live_status, live_error, live_progress, live_result = await pipe.execute()

            live_status_str = _redis_str(live_status) if live_status else None
            if live_status_str:
                if task.status in ("pending", "processing"):
                    if live_status_str != "done":
                        status = live_status_str
                else:
                    status = live_status_str

            if live_error:
                error_message = _redis_str(live_error)
            if live_progress:
                try:
                    progress = max(0, min(100, int(_redis_str(live_progress))))
                except (TypeError, ValueError):
                    pass

            redis_result_url = _parse_redis_result_url(live_result)
            if redis_result_url:
                result_url = redis_result_url

            if live_status_str == "done" and task.status in ("pending", "processing"):
                status = "done" if redis_result_url else "processing"
        except Exception:
            pass

    if status == "done" and not result_url:
        status = "processing"
    if status == "done":
        progress = 100

    latest_credits = await get_user_credits(db, current_user.id)

    return success(
        {
            "task_id": task.id,
            "status": status,
            "result_url": result_url,
            "prompt": task.prompt,
            "prompt_snapshot": parse_prompt_snapshot(task.prompt_snapshot_json),
            "settings_snapshot": parse_json_or_none(task.settings_snapshot_json),
            "input_mode": task.input_mode,
            "input_images": parse_json_or_none(task.input_images_json) or [],
            "duration": task.duration,
            "resolution": task.resolution,
            "aspect_ratio": task.aspect_ratio,
            "created_at": to_utc_iso(task.created_at),
            "error_message": error_message,
            "progress": progress,
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
