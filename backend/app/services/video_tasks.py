from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import parse_json_or_none
from app.core.prompt_snapshot import parse_prompt_snapshot
from app.core.task_state import merge_task_state
from app.core.task_timeout import project_task_runtime_state
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import get_user_credits
from app.models import VideoTask


async def get_user_video_task(
    db: AsyncSession,
    *,
    user_id: int,
    task_id: str,
) -> VideoTask | None:
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == task_id,
            VideoTask.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_video_task_details(
    db: AsyncSession,
    *,
    user_id: int,
    task_id: str,
    redis_pool: Any,
) -> dict[str, Any] | None:
    task = await get_user_video_task(db, user_id=user_id, task_id=task_id)
    if not task:
        return None

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
    latest_credits = await get_user_credits(db, user_id)

    return {
        "task_id": task.id,
        "scenario": task.scenario,
        "status": runtime.status,
        "result_url": runtime.result_url,
        "prompt": task.prompt,
        "prompt_snapshot": parse_prompt_snapshot(task.prompt_snapshot_json),
        "settings_snapshot": parse_json_or_none(task.settings_snapshot_json),
        "input_mode": task.input_mode,
        "input_images": parse_json_or_none(task.input_images_json) or [],
        "input_video_url": task.input_video_url,
        "duration": task.duration,
        "resolution": task.resolution,
        "aspect_ratio": task.aspect_ratio,
        "created_at": to_utc_iso(task.created_at),
        "error_message": runtime.error_message,
        "progress": runtime.progress,
        "credit_cost": task.credit_cost,
        "credits": latest_credits,
    }


async def archive_video_task(
    db: AsyncSession,
    *,
    user_id: int,
    task_id: str,
) -> str | None:
    task = await get_user_video_task(db, user_id=user_id, task_id=task_id)
    if not task:
        return "视频不存在"

    task.archived = True
    task.archived_at = utc_now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return "删除失败，请稍后重试"
    return None