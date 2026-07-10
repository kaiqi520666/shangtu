import asyncio
from datetime import timezone
import logging
import time
from typing import Any

import httpx
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.json_utils import parse_json_or_none
from app.core.logging_config import task_log_extra
from app.core.providers.heygen_provider import (
    create_avatar_video,
    create_video_translation,
    get_video,
    get_video_translation,
)
from app.core.task_state import set_task_progress, set_task_status
from app.core.time import utc_now
from app.models import VideoTask
from app.services.digital_human import settle_task_credits_if_needed
from app.services.heygen_task_lifecycle import (
    clean_text,
    provider_task_status,
    sync_video_job_status,
    task_progress,
)
from app.worker.task_failures import mark_video_failed, mark_video_timeout

logger = logging.getLogger("app.worker.heygen_tasks")
POLL_INTERVAL_SECONDS = 5
MAX_WAIT_SECONDS = 1800
MAX_TRANSIENT_ERRORS = 3


def _scene(task: VideoTask) -> dict:
    snapshot = parse_json_or_none(task.settings_snapshot_json) or {}
    scene = snapshot.get("scene")
    return scene if isinstance(scene, dict) else {}


def _first_string(data: Any, keys: set[str]) -> str:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and clean_text(value):
                return clean_text(value)
            nested = _first_string(value, keys)
            if nested:
                return nested
    elif isinstance(data, list):
        for value in data:
            nested = _first_string(value, keys)
            if nested:
                return nested
    return ""


def _task_extra(task: VideoTask, **values) -> dict:
    queue_duration_ms = None
    if getattr(task, "created_at", None):
        created_at = task.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        queue_duration_ms = (utc_now() - created_at).total_seconds() * 1000
    return task_log_extra(
        task_id=task.id,
        job_id=task.job_id,
        provider_task_id=values.pop("provider_task_id", task.provider_task_id),
        scenario=task.scenario,
        media_type="video",
        queue_duration_ms=values.pop("queue_duration_ms", queue_duration_ms),
        **values,
    )


async def _load_task(task_id: str, scenario: str) -> VideoTask | None:
    async with SessionLocal() as db:
        result = await db.execute(
            select(VideoTask).where(VideoTask.id == task_id, VideoTask.scenario == scenario)
        )
        return result.scalar_one_or_none()


async def _persist_provider_created(task_id: str, provider_task_id: str, status: str) -> None:
    async with SessionLocal() as db:
        task = await db.get(VideoTask, task_id)
        if not task:
            return
        task.provider_task_id = provider_task_id
        task.status = status
        task.progress = task_progress(status)
        await sync_video_job_status(db, job_id=task.job_id, scenario=task.scenario)
        await db.commit()


async def _persist_terminal(
    task_id: str,
    *,
    status: str,
    result_url: str | None,
    error_message: str | None,
    duration: int | None = None,
) -> None:
    async with SessionLocal() as db:
        task = await db.get(VideoTask, task_id)
        if not task:
            return
        task.status = status
        task.progress = task_progress(status)
        task.result_url = result_url
        task.error_message = error_message
        if duration is not None:
            task.duration = duration
        if status == "done" and task.scenario == "digital_human":
            settlement_started = time.monotonic()
            await settle_task_credits_if_needed(db, task)
            logger.info(
                "digital human credits settled",
                extra=_task_extra(
                    task,
                    event="settlement_completed",
                    phase="settlement",
                    status="done",
                    retry_count=0,
                    duration_ms=(time.monotonic() - settlement_started) * 1000,
                ),
            )
        await sync_video_job_status(db, job_id=task.job_id, scenario=task.scenario)
        await db.commit()


async def _mark_failed(ctx, task: VideoTask, message: str) -> None:
    await mark_video_failed(
        ctx["redis"],
        task.id,
        message,
        provider_task_id=task.provider_task_id,
    )
    async with SessionLocal() as db:
        await sync_video_job_status(db, job_id=task.job_id, scenario=task.scenario)
        await db.commit()


async def _mark_timeout(ctx, task: VideoTask, message: str) -> None:
    await mark_video_timeout(ctx["redis"], task.id, message)
    async with SessionLocal() as db:
        await sync_video_job_status(db, job_id=task.job_id, scenario=task.scenario)
        await db.commit()


async def _create_digital_human(task: VideoTask) -> str:
    scene = _scene(task)
    audio_mode = scene.get("audioMode") or "platform"
    async with httpx.AsyncClient(timeout=60) as client:
        data = await create_avatar_video(
            client,
            avatar_id=scene.get("avatarId") or "",
            title=task.title or "数字人视频",
            aspect_ratio=task.aspect_ratio,
            resolution=task.resolution,
            script=scene.get("script") if audio_mode == "platform" else None,
            voice_id=scene.get("voiceId") if audio_mode == "platform" else None,
            audio_url=scene.get("audioUrl") if audio_mode == "upload" else None,
            engine_type="avatar_iv" if task.type_id == "premium" else "avatar_iii",
            background_url=scene.get("backgroundUrl") or None,
            voice_settings=scene.get("voiceSettings") if audio_mode == "platform" else None,
            idempotency_key=task.id,
        )
    provider_task_id = clean_text(data.get("video_id"))
    if not provider_task_id:
        raise ValueError("HeyGen 未返回 video_id")
    status = provider_task_status(clean_text(data.get("status")))
    await _persist_provider_created(task.id, provider_task_id, status)
    return provider_task_id


async def _create_translation(task: VideoTask) -> str:
    scene = _scene(task)
    mode = "precision" if task.type_id == "premium" else "speed"
    async with httpx.AsyncClient(timeout=60) as client:
        data = await create_video_translation(
            client,
            video_url=task.input_video_url or scene.get("videoUrl") or "",
            title=task.title or "视频翻译",
            output_language=scene.get("targetLanguageName") or "",
            mode=mode,
            idempotency_key=task.id,
        )
    provider_task_id = _first_string(
        data,
        {"video_translation_id", "video_translate_id", "translation_id", "task_id", "id"},
    )
    if not provider_task_id:
        raise ValueError("HeyGen 未返回视频翻译任务 ID")
    status = provider_task_status(_first_string(data, {"status", "video_status", "translation_status"}))
    await _persist_provider_created(task.id, provider_task_id, status)
    return provider_task_id


async def _poll_digital_human(provider_task_id: str) -> tuple[str, str | None, str | None, int | None]:
    async with httpx.AsyncClient(timeout=60) as client:
        data = await get_video(client, video_id=provider_task_id)
    result_url = clean_text(data.get("video_url") or data.get("url") or data.get("result_url")) or None
    error = clean_text(data.get("error_message") or data.get("failure_reason") or data.get("message")) or None
    status = provider_task_status(
        clean_text(data.get("status") or data.get("video_status")),
        video_url=result_url,
        failure_message=error,
    )
    if status == "done" and not result_url:
        status = "processing"
    try:
        duration = max(0, int(float(data.get("duration") or data.get("video_duration") or 0)))
    except (TypeError, ValueError):
        duration = None
    return status, result_url, error, duration


async def _poll_translation(provider_task_id: str) -> tuple[str, str | None, str | None, int | None]:
    async with httpx.AsyncClient(timeout=60) as client:
        data = await get_video_translation(client, video_translation_id=provider_task_id)
    result_url = _first_string(
        data,
        {"video_url", "url", "result_url", "output_url", "translated_video_url"},
    ) or None
    error = _first_string(data, {"error_message", "failure_reason", "message"}) or None
    status = provider_task_status(
        _first_string(data, {"status", "video_status", "translation_status"}),
        video_url=result_url,
        failure_message=error,
    )
    if status == "done" and not result_url:
        status = "processing"
    return status, result_url, error, None


async def _run_heygen_task(ctx, task_id: str, scenario: str) -> None:
    task = await _load_task(task_id, scenario)
    if not task or task.archived or task.status in {"done", "failed", "timeout"}:
        return
    started = time.monotonic()
    logger.info(
        "heygen task started",
        extra=_task_extra(
            task,
            event="task_started",
            phase="queue",
            status="processing",
            retry_count=0,
            duration_ms=0,
        ),
    )
    transient_errors = 0
    try:
        provider_task_id = task.provider_task_id
        create_started = time.monotonic()
        while not provider_task_id:
            try:
                provider_task_id = (
                    await _create_digital_human(task)
                    if scenario == "digital_human"
                    else await _create_translation(task)
                )
            except (httpx.HTTPError, OSError):
                transient_errors += 1
                logger.warning(
                    "heygen provider create retry",
                    extra=_task_extra(
                        task,
                        event="provider_create_retry",
                        phase="provider_create",
                        status="processing",
                        retry_count=transient_errors,
                        duration_ms=(time.monotonic() - create_started) * 1000,
                    ),
                )
                if transient_errors >= MAX_TRANSIENT_ERRORS:
                    raise
                await asyncio.sleep(POLL_INTERVAL_SECONDS * transient_errors)

        task.provider_task_id = provider_task_id
        logger.info(
            "heygen provider task created",
            extra=_task_extra(
                task,
                event="provider_created",
                provider_task_id=provider_task_id,
                phase="provider_create",
                status="processing",
                retry_count=transient_errors,
                duration_ms=(time.monotonic() - create_started) * 1000,
            ),
        )

        await set_task_status(ctx["redis"], "video", task_id, "processing", ttl=7200)
        await set_task_progress(ctx["redis"], "video", task_id, 65)
        provider_wait_started = time.monotonic()
        transient_errors = 0
        while time.monotonic() - provider_wait_started < MAX_WAIT_SECONDS:
            try:
                status, result_url, error, duration = (
                    await _poll_digital_human(provider_task_id)
                    if scenario == "digital_human"
                    else await _poll_translation(provider_task_id)
                )
                transient_errors = 0
            except (httpx.HTTPError, OSError):
                transient_errors += 1
                logger.warning(
                    "heygen provider poll retry",
                    extra=_task_extra(
                        task,
                        event="provider_poll_retry",
                        provider_task_id=provider_task_id,
                        phase="provider_poll",
                        status="processing",
                        retry_count=transient_errors,
                        duration_ms=(time.monotonic() - provider_wait_started) * 1000,
                    ),
                )
                if transient_errors >= MAX_TRANSIENT_ERRORS:
                    raise
                await asyncio.sleep(POLL_INTERVAL_SECONDS * transient_errors)
                continue
            if status == "done":
                await _persist_terminal(
                    task_id,
                    status="done",
                    result_url=result_url,
                    error_message=None,
                    duration=duration,
                )
                await set_task_status(ctx["redis"], "video", task_id, "done", ttl=86400)
                await set_task_progress(ctx["redis"], "video", task_id, 100)
                logger.info(
                    "heygen provider task completed",
                    extra=_task_extra(
                        task,
                        event="provider_completed",
                        provider_task_id=provider_task_id,
                        phase="provider_poll",
                        status="done",
                        retry_count=transient_errors,
                        duration_ms=(time.monotonic() - provider_wait_started) * 1000,
                    ),
                )
                return
            if status == "failed":
                logger.error(
                    "heygen task failed: %s",
                    error or "HeyGen 任务失败",
                    extra=_task_extra(
                        task,
                        event="task_failed",
                        provider_task_id=provider_task_id,
                        phase="provider_poll",
                        status="failed",
                        retry_count=transient_errors,
                        duration_ms=(time.monotonic() - started) * 1000,
                    ),
                )
                await _mark_failed(ctx, task, error or "HeyGen 任务失败")
                return
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        logger.warning(
            "heygen task timeout",
            extra=_task_extra(
                task,
                event="task_timeout",
                provider_task_id=provider_task_id,
                phase="provider_poll",
                status="timeout",
                retry_count=transient_errors,
                duration_ms=(time.monotonic() - started) * 1000,
            ),
        )
        await _mark_timeout(ctx, task, "HeyGen 任务处理超时")
    except Exception as exc:
        logger.exception(
            "heygen task failed: %s",
            exc,
            extra=_task_extra(
                task,
                event="task_failed",
                phase="unexpected",
                status="failed",
                retry_count=transient_errors,
                duration_ms=(time.monotonic() - started) * 1000,
            ),
        )
        await _mark_failed(ctx, task, str(exc) or "HeyGen 任务创建失败")


async def submit_digital_human_task(ctx, task_id: str) -> None:
    await _run_heygen_task(ctx, task_id, "digital_human")


async def submit_video_translation_task(ctx, task_id: str) -> None:
    await _run_heygen_task(ctx, task_id, "video_translation")
