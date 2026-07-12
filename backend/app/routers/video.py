from fastapi import APIRouter, Depends, File, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.media_download import remote_media_download_response
from app.core.strategy.dashscope_client import (
    DashScopeConfigError,
    optimize_free_video_prompt,
)
from app.core.prompt_template_builder import build_strategy_template_prompt
from app.core.system_settings import get_effective_video_credit_costs
from app.core.video_strategy_generation import generate_video_strategy
from app.models import User
from app.schemas.response import Response, fail, success
from app.services.video_assets import create_reference_audio, create_uploaded_video
from app.services.video_generation import (
    VideoGeneratePayload,
    clean_urls,
    create_video_generation_task,
    validate_aspect_ratio,
    validate_video_duration,
    validate_video_inputs,
)
from app.services.video_tasks import (
    archive_video_task,
    get_user_video_task,
    get_video_task_details,
)

router = APIRouter(prefix="/video", tags=["视频生成"])

class VideoGenerateRequest(BaseModel):
    scenario: str = "product_video"
    type_id: str
    title: str | None = None
    input_mode: str = "reference_to_video"
    image_urls: list[str] = Field(default_factory=list)
    input_video_url: str | None = None
    video_urls: list[str] = Field(default_factory=list)
    audio_urls: list[str] = Field(default_factory=list)
    user_prompt: str | None = None
    duration: int = 8
    resolution: str = "720p"
    aspect_ratio: str = "9:16"
    generate_audio: bool = False
    enable_web_search: bool = False
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
    duration: int = 8
    aspect_ratio: str = "9:16"
    product_input: str = ""


class FreeVideoOptimizeRequest(BaseModel):
    prompt: str


@router.get("/credit-costs", response_model=Response)
async def video_credit_costs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        costs = await get_effective_video_credit_costs(db)
    except ValueError as exc:
        return fail(str(exc))
    return success({"costs": costs, "consumption_multiplier": float(current_user.consumption_multiplier)})


@router.post("/strategy", response_model=Response)
async def video_strategy(
    req: VideoStrategyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    images = [item.model_dump() for item in req.images]
    image_urls = clean_urls([item["url"] for item in images])
    input_error = validate_video_inputs(req.input_mode, image_urls)
    if input_error:
        return fail(input_error)

    aspect_ratio = str(req.aspect_ratio or "").strip()
    aspect_error = validate_aspect_ratio(aspect_ratio)
    if aspect_error:
        return fail(aspect_error)
    duration_error = validate_video_duration(req.duration)
    if duration_error:
        return fail(duration_error)

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


@router.post("/upload", response_model=Response)
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        content = await file.read()
        outcome = await create_uploaded_video(
            db,
            user_id=current_user.id,
            content=content,
            content_type=file.content_type or "",
            filename=file.filename,
        )
    except Exception:
        return fail("视频上传失败")
    finally:
        await file.close()
    if outcome.error_message:
        return fail(outcome.error_message)
    uploaded = outcome.uploaded
    return success(
        {
            "url": uploaded.url,
            "object_key": uploaded.object_key,
            "content_type": uploaded.content_type,
            "size": uploaded.size,
        }
    )


@router.post("/audio-upload", response_model=Response)
async def upload_reference_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        content = await file.read()
        outcome = await create_reference_audio(
            db,
            user_id=current_user.id,
            content=content,
            content_type=file.content_type or "",
            filename=file.filename,
        )
    except Exception:
        return fail("音频上传失败")
    finally:
        await file.close()
    if outcome.error_message:
        return fail(outcome.error_message)
    uploaded = outcome.uploaded
    return success(
        {
            "url": uploaded.url,
            "object_key": uploaded.object_key,
            "content_type": uploaded.content_type,
            "size": uploaded.size,
            "asset_id": outcome.asset_id,
        }
    )


@router.post("/generate", response_model=Response)
async def create_video_task(
    req: VideoGenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result, failure = await create_video_generation_task(
        db=db,
        current_user=current_user,
        payload=VideoGeneratePayload(
            scenario=req.scenario, type_id=req.type_id, title=req.title,
            input_mode=req.input_mode, image_urls=req.image_urls,
            input_video_url=req.input_video_url, video_urls=req.video_urls,
            audio_urls=req.audio_urls, user_prompt=req.user_prompt,
            duration=req.duration, resolution=req.resolution,
            aspect_ratio=req.aspect_ratio, generate_audio=req.generate_audio,
            enable_web_search=req.enable_web_search,
            settings_snapshot=req.settings_snapshot, sort_order=req.sort_order,
            job_id=req.job_id,
        ),
        get_redis_pool=lambda: request.app.state.redis_pool,
    )
    if failure is not None:
        return failure
    return success({"task_id": result.task_id, "credits": result.credits, "credit_cost": result.credit_cost})


@router.get("/task/{task_id}", response_model=Response)
async def get_video_task(
    task_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    details = await get_video_task_details(
        db,
        user_id=current_user.id,
        task_id=task_id,
        redis_pool=getattr(request.app.state, "redis_pool", None),
    )
    if details is None:
        return fail("视频任务不存在")
    return success(details)


@router.delete("/task/{task_id}", response_model=Response)
async def delete_video_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    error_message = await archive_video_task(
        db,
        user_id=current_user.id,
        task_id=task_id,
    )
    if error_message:
        return fail(error_message)
    return success({"task_id": task_id})


@router.get("/task/{task_id}/download")
async def download_video_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_user_video_task(
        db,
        user_id=current_user.id,
        task_id=task_id,
    )
    if not task or not task.result_url:
        return fail("视频不存在或尚未生成完成")

    return remote_media_download_response(
        task.result_url,
        filename_stem=task_id,
        fallback_extension="mp4",
    )
