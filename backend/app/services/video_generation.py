import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import normalize_video_resolution
from app.core.json_utils import dump_json_or_none
from app.core.prompt_snapshot import dump_prompt_snapshot
from app.core.scenarios import SCENARIO_TITLE_PREFIX, VIDEO_SCENARIOS
from app.core.system_settings import get_effective_video_credit_cost
from app.core.user_credits import refund_user_credits
from app.core.video_prompt_builder import build_video_generate_prompt
from app.models import GenerationJob, User, VideoTask
from app.schemas.response import Response, fail
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate

VIDEO_INPUT_MODES = {"reference_to_video", "multimodal_reference"}
VIDEO_ASPECT_RATIOS = {"16:9", "9:16", "1:1", "4:3", "3:4"}
VIDEO_DURATIONS = {4, 8, 10, 12, 15}
FREE_VIDEO_RESOLUTIONS = {"720p", "1080p"}


@dataclass(slots=True)
class VideoGeneratePayload:
    scenario: str
    type_id: str
    title: str | None
    input_mode: str
    image_urls: list[str]
    input_video_url: str | None
    video_urls: list[str]
    audio_urls: list[str]
    user_prompt: str | None
    duration: int
    resolution: str
    aspect_ratio: str
    generate_audio: bool
    enable_web_search: bool
    settings_snapshot: dict | None
    sort_order: int
    job_id: str | None


@dataclass(slots=True)
class VideoGenerateResult:
    task_id: str
    credits: int
    credit_cost: int


@dataclass(slots=True)
class PreparedVideo:
    scenario: str
    input_mode: str
    image_urls: list[str]
    input_video_url: str
    video_urls: list[str]
    audio_urls: list[str]
    resolution: str
    aspect_ratio: str


@dataclass(slots=True)
class VideoGenerationContext:
    prepared: PreparedVideo
    job: GenerationJob | None
    prompt: str
    prompt_snapshot: dict
    settings_snapshot: dict
    base_credit_cost: int


def clean_urls(urls: list[str]) -> list[str]:
    return [str(url).strip() for url in urls if str(url).strip()]


def validate_video_inputs(input_mode: str, image_urls: list[str]) -> str | None:
    if input_mode not in VIDEO_INPUT_MODES:
        return "不支持的视频素材模式"
    if input_mode == "reference_to_video" and not 1 <= len(image_urls) <= 9:
        return "商品视频必须上传 1-9 张参考图"
    return None


def validate_aspect_ratio(aspect_ratio: str) -> str | None:
    if aspect_ratio not in VIDEO_ASPECT_RATIOS:
        supported = " / ".join(sorted(VIDEO_ASPECT_RATIOS))
        return f"不支持的视频比例：{aspect_ratio}，请选择 {supported}"
    return None


def validate_video_duration(duration: int) -> str | None:
    if duration not in VIDEO_DURATIONS:
        supported = " / ".join(str(item) for item in sorted(VIDEO_DURATIONS))
        return f"不支持的视频时长：{duration}秒，请选择 {supported} 秒"
    return None


def _prepare_payload(payload: VideoGeneratePayload) -> PreparedVideo:
    scenario = (payload.scenario or "product_video").strip() or "product_video"
    if scenario not in VIDEO_SCENARIOS:
        raise ValueError("不支持的视频场景")
    prepared = PreparedVideo(
        scenario=scenario,
        input_mode="multimodal_reference" if scenario == "free_video" else payload.input_mode,
        image_urls=clean_urls(payload.image_urls),
        input_video_url=str(payload.input_video_url or "").strip(),
        video_urls=clean_urls(payload.video_urls),
        audio_urls=clean_urls(payload.audio_urls),
        resolution=normalize_video_resolution(payload.resolution),
        aspect_ratio=str(payload.aspect_ratio or "").strip(),
    )
    errors = []
    if scenario == "free_video":
        if not str(payload.user_prompt or "").strip():
            errors.append("请输入视频提示词")
        limits = ((prepared.image_urls, 9, "参考图"), (prepared.video_urls, 3, "参考视频"), (prepared.audio_urls, 3, "参考音频"))
        errors.extend(f"{label}最多只能上传 {limit} 张" if label == "参考图" else f"{label}最多只能上传 {limit} 条" for items, limit, label in limits if len(items) > limit)
        if prepared.resolution not in FREE_VIDEO_RESOLUTIONS:
            errors.append("自由生视频清晰度请选择 720p / 1080p")
    else:
        errors.append(validate_video_inputs(payload.input_mode, prepared.image_urls))
    errors.extend(
        [
            validate_aspect_ratio(prepared.aspect_ratio),
            validate_video_duration(payload.duration),
        ]
    )
    error = next((item for item in errors if item), None)
    if error:
        raise ValueError(error)
    return prepared


async def _get_job(
    db: AsyncSession,
    *,
    job_id: str | None,
    user_id: int,
    scenario: str,
) -> GenerationJob | None:
    if not job_id:
        return None
    result = await db.execute(
        select(GenerationJob).where(
            GenerationJob.id == job_id,
            GenerationJob.user_id == user_id,
            GenerationJob.scenario == scenario,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise ValueError("任务不存在")
    return job


def _settings_snapshot(payload: VideoGeneratePayload, prepared: PreparedVideo) -> dict:
    return {
        **(payload.settings_snapshot or {}),
        "scenario": prepared.scenario,
        "type_id": payload.type_id,
        "title": payload.title,
        "input_mode": prepared.input_mode,
        "input_video_url": prepared.input_video_url,
        "video_urls": prepared.video_urls,
        "audio_urls": prepared.audio_urls,
        "duration": payload.duration,
        "resolution": prepared.resolution,
        "aspect_ratio": prepared.aspect_ratio,
        "generate_audio": payload.generate_audio,
        "enable_web_search": payload.enable_web_search,
    }


async def _prepare_generation(
    db: AsyncSession,
    current_user: User,
    payload: VideoGeneratePayload,
) -> VideoGenerationContext:
    prepared = _prepare_payload(payload)
    base_credit_cost = await get_effective_video_credit_cost(db, prepared.resolution, payload.duration)
    job = await _get_job(
        db,
        job_id=payload.job_id,
        user_id=current_user.id,
        scenario=prepared.scenario,
    )
    settings_snapshot = _settings_snapshot(payload, prepared)
    built_prompt = await build_video_generate_prompt(
        db,
        type_id=payload.type_id,
        title=payload.title,
        user_prompt=payload.user_prompt,
        settings=settings_snapshot,
    )
    return VideoGenerationContext(
        prepared=prepared,
        job=job,
        prompt=built_prompt.final_prompt,
        prompt_snapshot=built_prompt.prompt_snapshot,
        settings_snapshot=settings_snapshot,
        base_credit_cost=base_credit_cost,
    )


def _consume_note(payload: VideoGeneratePayload, context: VideoGenerationContext) -> str:
    parts = [SCENARIO_TITLE_PREFIX.get(context.prepared.scenario, "视频生成")]
    if str(payload.title or "").strip():
        parts.append(payload.title.strip())
    mode_label = {
        "reference_to_video": "参考图生视频",
        "multimodal_reference": "多模态参考生视频",
    }.get(context.prepared.input_mode, context.prepared.input_mode)
    parts.extend([mode_label, context.prepared.resolution, f"{payload.duration}秒"])
    return " · ".join(parts)


async def _create_charged_task(
    db: AsyncSession,
    current_user: User,
    payload: VideoGeneratePayload,
    context: VideoGenerationContext,
) -> tuple[VideoTask | None, int, Response | None]:
    charge, failure = await deduct_credits_or_fail(
        db,
        current_user.id,
        context.base_credit_cost,
        note=_consume_note(payload, context),
    )
    if failure is not None:
        return None, 0, failure
    prepared = context.prepared
    task = VideoTask(
        id=str(uuid.uuid4()), user_id=current_user.id,
        job_id=context.job.id if context.job else None,
        scenario=prepared.scenario, type_id=payload.type_id, title=payload.title,
        sort_order=payload.sort_order, prompt=context.prompt,
        input_mode=prepared.input_mode,
        input_images_json=dump_json_or_none(prepared.image_urls),
        input_video_url=(prepared.video_urls[0] if prepared.scenario == "free_video" and prepared.video_urls else prepared.input_video_url) or None,
        duration=payload.duration, resolution=prepared.resolution,
        aspect_ratio=prepared.aspect_ratio, status="pending",
        prompt_snapshot_json=dump_prompt_snapshot(context.prompt_snapshot),
        settings_snapshot_json=dump_json_or_none(context.settings_snapshot),
        credit_cost=charge.cost,
    )
    db.add(task)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return None, 0, fail("视频任务创建失败，请稍后重试")
    return task, charge.balance_after, None


async def _enqueue_task(
    *,
    db: AsyncSession,
    task: VideoTask,
    payload: VideoGeneratePayload,
    context: VideoGenerationContext,
    remaining_credits: int,
    get_redis_pool: Callable[[], Any],
) -> Response | None:
    async def mark_failed(_refunded_credits: int) -> None:
        await db.execute(
            update(VideoTask).where(VideoTask.id == task.id).values(status="failed", credit_refunded=True)
        )

    prepared = context.prepared
    return await enqueue_or_compensate(
        get_redis_pool=get_redis_pool, db=db, job_name="generate_video",
        job_args=(task.id, context.prompt, payload.duration, prepared.aspect_ratio,
                  prepared.resolution, prepared.image_urls, prepared.input_video_url,
                  prepared.video_urls, prepared.audio_urls, payload.generate_audio,
                  payload.enable_web_search),
        user_id=task.user_id, credit_cost=task.credit_cost,
        remaining_credits=remaining_credits, refund_credits=refund_user_credits,
        mark_failed=mark_failed, failure_message="视频任务入队失败，请稍后重试",
        failure_data={"task_id": task.id}, refund_note=f"视频任务入队失败退回 · {task.id}",
    )


async def _mark_job_generating(db: AsyncSession, job: GenerationJob | None) -> None:
    if job is None or job.status == "generating":
        return
    try:
        await db.execute(update(GenerationJob).where(GenerationJob.id == job.id).values(status="generating"))
        await db.commit()
    except Exception:
        await db.rollback()


async def create_video_generation_task(
    *,
    db: AsyncSession,
    current_user: User,
    payload: VideoGeneratePayload,
    get_redis_pool: Callable[[], Any],
) -> tuple[VideoGenerateResult | None, Response | None]:
    try:
        context = await _prepare_generation(db, current_user, payload)
    except ValueError as exc:
        return None, fail(str(exc))
    task, remaining_credits, failure = await _create_charged_task(db, current_user, payload, context)
    if failure is not None:
        return None, failure
    failure = await _enqueue_task(
        db=db, task=task, payload=payload, context=context,
        remaining_credits=remaining_credits, get_redis_pool=get_redis_pool,
    )
    if failure is not None:
        return None, failure
    await _mark_job_generating(db, context.job)
    return VideoGenerateResult(task.id, remaining_credits, task.credit_cost), None
