from dataclasses import dataclass
from datetime import datetime

from app.core.json_utils import parse_json_object
from app.core.providers.toapis_provider import (
    MAX_WAIT_SECONDS,
    POLL_INTERVAL_SECONDS,
    VIDEO_MAX_WAIT_SECONDS,
    VIDEO_POLL_INTERVAL_SECONDS,
)
from app.core.time import utc_now

PROCESSING_TASK_STATUSES = {"pending", "processing"}
IMAGE_TASK_STALE_TIMEOUT_SECONDS = MAX_WAIT_SECONDS + max(120, POLL_INTERVAL_SECONDS * 3)
VIDEO_TASK_STALE_TIMEOUT_SECONDS = VIDEO_MAX_WAIT_SECONDS + max(180, VIDEO_POLL_INTERVAL_SECONDS * 3)


@dataclass
class ProjectedTaskRuntimeState:
    status: str
    error_message: str | None
    progress: int
    result_url: str | None


def user_visible_task_error(error_message: str | None) -> str | None:
    if not error_message:
        return error_message
    payload = parse_json_object(error_message)
    message = payload.get("message")
    return message if isinstance(message, str) and message else error_message


def stale_timeout_seconds(media_type: str) -> int:
    if media_type == "video":
        return VIDEO_TASK_STALE_TIMEOUT_SECONDS
    return IMAGE_TASK_STALE_TIMEOUT_SECONDS


def stale_timeout_message(media_type: str) -> str:
    if media_type == "video":
        return "视频任务长时间无进展，已自动标记为超时，请稍后重试"
    return "图片任务长时间无进展，已自动标记为超时，请稍后重试"


def is_stale_processing_task(
    media_type: str,
    *,
    status: str,
    created_at: datetime | None,
    result_url: str | None = None,
    now: datetime | None = None,
) -> bool:
    if status not in PROCESSING_TASK_STATUSES:
        return False
    if result_url:
        return False
    if created_at is None:
        return False
    current_time = now or utc_now()
    age_seconds = (current_time - created_at).total_seconds()
    return age_seconds >= stale_timeout_seconds(media_type)


def project_task_runtime_state(
    media_type: str,
    *,
    status: str,
    error_message: str | None,
    progress: int | None,
    result_url: str | None,
    created_at: datetime | None,
    now: datetime | None = None,
) -> ProjectedTaskRuntimeState:
    normalized_status = status or "pending"
    normalized_progress = int(progress or 0)
    normalized_error = user_visible_task_error(error_message)
    if is_stale_processing_task(
        media_type,
        status=normalized_status,
        created_at=created_at,
        result_url=result_url,
        now=now,
    ):
        normalized_status = "timeout"
        normalized_error = normalized_error or stale_timeout_message(media_type)
    return ProjectedTaskRuntimeState(
        status=normalized_status,
        error_message=normalized_error,
        progress=normalized_progress,
        result_url=result_url,
    )
