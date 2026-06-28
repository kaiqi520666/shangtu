from sqlalchemy import Integer, String, cast, func, literal, select

from app.core.json_utils import parse_json_or_none
from app.core.prompt_snapshot import parse_prompt_snapshot
from app.core.scenarios import VIDEO_SCENARIOS
from app.core.task_timeout import project_task_runtime_state, user_visible_task_error
from app.core.time import to_utc_iso
from app.models import GenerationJob, ImageTask, User, VideoTask


def image_task_payload(task: ImageTask) -> dict:
    runtime = project_task_runtime_state(
        "image",
        status=task.status,
        error_message=task.error_message,
        progress=task.progress,
        result_url=task.result_url,
        created_at=task.created_at,
    )
    return {
        "task_id": task.id,
        "media_type": "image",
        "type_id": task.type_id,
        "title": task.title,
        "sort_order": task.sort_order,
        "status": runtime.status,
        "progress": runtime.progress,
        "result_url": runtime.result_url,
        "size": task.size,
        "error_message": runtime.error_message,
        "credit_cost": task.credit_cost,
        "credit_refunded": bool(task.credit_refunded),
        "replaced_by_task_id": task.replaced_by_task_id,
        "prompt": task.prompt,
        "prompt_snapshot": parse_prompt_snapshot(task.prompt_snapshot_json),
        "settings_snapshot": parse_json_or_none(task.settings_snapshot_json),
    }


def video_task_payload(task: VideoTask) -> dict:
    runtime = project_task_runtime_state(
        "video",
        status=task.status,
        error_message=task.error_message,
        progress=task.progress,
        result_url=task.result_url,
        created_at=task.created_at,
    )
    return {
        "task_id": task.id,
        "media_type": "video",
        "scenario": task.scenario,
        "type_id": task.type_id,
        "title": task.title,
        "sort_order": task.sort_order,
        "status": runtime.status,
        "progress": runtime.progress,
        "result_url": runtime.result_url,
        "input_mode": task.input_mode,
        "input_images": parse_json_or_none(task.input_images_json) or [],
        "duration": task.duration,
        "resolution": task.resolution,
        "aspect_ratio": task.aspect_ratio,
        "error_message": runtime.error_message,
        "credit_cost": task.credit_cost,
        "credit_refunded": bool(task.credit_refunded),
        "prompt": task.prompt,
        "prompt_snapshot": parse_prompt_snapshot(task.prompt_snapshot_json),
        "settings_snapshot": parse_json_or_none(task.settings_snapshot_json),
    }


def image_asset_select(user_id: int, scenario: str | None):
    if scenario in VIDEO_SCENARIOS:
        return None
    stmt = (
        select(
            ImageTask.id.label("task_id"),
            literal("image").label("media_type"),
            ImageTask.result_url.label("result_url"),
            ImageTask.title.label("title"),
            ImageTask.type_id.label("type_id"),
            func.coalesce(GenerationJob.scenario, literal("")).label("scenario"),
            func.coalesce(GenerationJob.title, literal("")).label("job_title"),
            ImageTask.created_at.label("created_at"),
        )
        .outerjoin(GenerationJob, GenerationJob.id == ImageTask.job_id)
        .where(
            ImageTask.user_id == user_id,
            ImageTask.status == "done",
            ImageTask.archived.is_(False),
        )
    )
    if scenario:
        stmt = stmt.where(ImageTask.job_id.isnot(None), GenerationJob.scenario == scenario)
    return stmt


def video_asset_select(user_id: int, scenario: str | None):
    if scenario and scenario not in VIDEO_SCENARIOS:
        return None
    stmt = (
        select(
            VideoTask.id.label("task_id"),
            literal("video").label("media_type"),
            VideoTask.result_url.label("result_url"),
            VideoTask.title.label("title"),
            VideoTask.type_id.label("type_id"),
            VideoTask.scenario.label("scenario"),
            func.coalesce(GenerationJob.title, literal("")).label("job_title"),
            VideoTask.created_at.label("created_at"),
        )
        .outerjoin(GenerationJob, GenerationJob.id == VideoTask.job_id)
        .where(
            VideoTask.user_id == user_id,
            VideoTask.status == "done",
            VideoTask.archived.is_(False),
        )
    )
    if scenario:
        stmt = stmt.where(VideoTask.scenario == scenario)
    return stmt


def image_admin_select():
    return (
        select(
            ImageTask.id.label("id"),
            literal("image").label("media_type"),
            ImageTask.user_id.label("user_id"),
            User.email.label("user_email"),
            ImageTask.job_id.label("job_id"),
            GenerationJob.title.label("job_title"),
            GenerationJob.scenario.label("scenario"),
            ImageTask.type_id.label("type_id"),
            ImageTask.title.label("title"),
            ImageTask.size.label("size"),
            cast(literal(None), String).label("input_mode"),
            cast(literal(None), Integer).label("duration"),
            cast(literal(None), String).label("resolution"),
            cast(literal(None), String).label("aspect_ratio"),
            ImageTask.status.label("status"),
            ImageTask.progress.label("progress"),
            ImageTask.provider.label("provider"),
            ImageTask.provider_task_id.label("provider_task_id"),
            ImageTask.credit_cost.label("credit_cost"),
            ImageTask.credit_refunded.label("credit_refunded"),
            ImageTask.result_url.label("result_url"),
            ImageTask.error_message.label("error_message"),
            ImageTask.archived.label("archived"),
            ImageTask.created_at.label("created_at"),
        )
        .join(User, User.id == ImageTask.user_id)
        .outerjoin(GenerationJob, GenerationJob.id == ImageTask.job_id)
    )


def video_admin_select():
    size_expr = (
        VideoTask.aspect_ratio
        + literal("/")
        + VideoTask.resolution
        + literal("/")
        + cast(VideoTask.duration, String)
        + literal("s")
    )
    return (
        select(
            VideoTask.id.label("id"),
            literal("video").label("media_type"),
            VideoTask.user_id.label("user_id"),
            User.email.label("user_email"),
            VideoTask.job_id.label("job_id"),
            GenerationJob.title.label("job_title"),
            VideoTask.scenario.label("scenario"),
            VideoTask.type_id.label("type_id"),
            VideoTask.title.label("title"),
            size_expr.label("size"),
            VideoTask.input_mode.label("input_mode"),
            VideoTask.duration.label("duration"),
            VideoTask.resolution.label("resolution"),
            VideoTask.aspect_ratio.label("aspect_ratio"),
            VideoTask.status.label("status"),
            VideoTask.progress.label("progress"),
            VideoTask.provider.label("provider"),
            VideoTask.provider_task_id.label("provider_task_id"),
            VideoTask.credit_cost.label("credit_cost"),
            VideoTask.credit_refunded.label("credit_refunded"),
            VideoTask.result_url.label("result_url"),
            VideoTask.error_message.label("error_message"),
            VideoTask.archived.label("archived"),
            VideoTask.created_at.label("created_at"),
        )
        .join(User, User.id == VideoTask.user_id)
        .outerjoin(GenerationJob, GenerationJob.id == VideoTask.job_id)
    )


def admin_task_payload(row) -> dict:
    return {
        "id": row["id"],
        "media_type": row["media_type"],
        "user_id": row["user_id"],
        "user_email": row["user_email"],
        "job_id": row["job_id"],
        "job_title": row["job_title"],
        "scenario": row["scenario"],
        "type_id": row["type_id"],
        "title": row["title"],
        "size": row["size"],
        "input_mode": row["input_mode"],
        "duration": row["duration"],
        "resolution": row["resolution"],
        "aspect_ratio": row["aspect_ratio"],
        "status": row["status"],
        "progress": row["progress"],
        "provider": row["provider"],
        "provider_task_id": row["provider_task_id"],
        "credit_cost": row["credit_cost"],
        "credit_refunded": row["credit_refunded"],
        "result_url": row["result_url"],
        "error_message": user_visible_task_error(row["error_message"]),
        "archived": row["archived"],
        "created_at": to_utc_iso(row["created_at"]),
    }


def includes_image(media_type: str | None) -> bool:
    return media_type in (None, "", "image")


def includes_video(media_type: str | None) -> bool:
    return media_type in (None, "", "video")
