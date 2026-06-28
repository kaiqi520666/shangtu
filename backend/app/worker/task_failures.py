import logging

from app.core.task_state import set_task_error, set_task_status
from app.worker.provider_errors import normalize_provider_error
from app.worker.task_state_sync import refund_generation_credit, update_generation_task_in_db

logger = logging.getLogger("app.worker.tasks")


async def mark_terminal(
    redis,
    media_type: str,
    task_id: str,
    raw_message: str,
    *,
    status: str,
) -> None:
    logger.warning(
        "generation %s %s (raw): %s",
        media_type,
        status,
        raw_message,
        extra={"task_id": task_id, "media_type": media_type, "status": status},
    )
    friendly = normalize_provider_error(raw_message, media_type=media_type)
    await update_generation_task_in_db(media_type, task_id, status=status, error_message=friendly)
    await refund_generation_credit(media_type, task_id)
    await set_task_error(redis, media_type, task_id, friendly)
    await set_task_status(redis, media_type, task_id, status, ttl=3600)


async def mark_failed(redis, task_id: str, raw_message: str) -> None:
    await mark_terminal(redis, "image", task_id, raw_message, status="failed")


async def mark_timeout(redis, task_id: str, raw_message: str) -> None:
    await mark_terminal(redis, "image", task_id, raw_message, status="timeout")


async def mark_video_failed(redis, task_id: str, raw_message: str) -> None:
    await mark_terminal(redis, "video", task_id, raw_message, status="failed")


async def mark_video_timeout(redis, task_id: str, raw_message: str) -> None:
    await mark_terminal(redis, "video", task_id, raw_message, status="timeout")
