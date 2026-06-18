from fastapi import APIRouter, Depends
from sqlalchemy import Integer, String, cast, false, func, literal, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.time import to_utc_iso
from app.models import GenerationJob, ImageTask, User, VideoTask
from app.schemas.response import Response, success

from .utils import page_payload

router = APIRouter()


def _image_task_select():
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


def _video_task_select():
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
            func.coalesce(GenerationJob.scenario, literal("product_video")).label("scenario"),
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


def _admin_task_payload(row) -> dict:
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
        "error_message": row["error_message"],
        "archived": row["archived"],
        "created_at": to_utc_iso(row["created_at"]),
    }


@router.get("/image-tasks", response_model=Response)
async def list_image_tasks(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    scenario: str | None = None,
    media_type: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    image_stmt = _image_task_select()
    video_stmt = _video_task_select()
    if status in {"pending", "processing", "done", "failed", "timeout"}:
        image_stmt = image_stmt.where(ImageTask.status == status)
        video_stmt = video_stmt.where(VideoTask.status == status)
    if scenario in {"product_suite", "product_image", "outfit", "free_image"}:
        image_stmt = image_stmt.where(GenerationJob.scenario == scenario)
        video_stmt = video_stmt.where(false())
    elif scenario == "product_video":
        image_stmt = image_stmt.where(false())
    if keyword:
        like = f"%{keyword.strip()}%"
        image_stmt = image_stmt.where(
            or_(
                ImageTask.id.ilike(like),
                ImageTask.title.ilike(like),
                ImageTask.type_id.ilike(like),
                ImageTask.provider_task_id.ilike(like),
                User.email.ilike(like),
                GenerationJob.title.ilike(like),
            )
        )
        video_stmt = video_stmt.where(
            or_(
                VideoTask.id.ilike(like),
                VideoTask.title.ilike(like),
                VideoTask.type_id.ilike(like),
                VideoTask.provider_task_id.ilike(like),
                User.email.ilike(like),
                GenerationJob.title.ilike(like),
            )
        )

    selects = []
    if media_type in (None, "", "image"):
        selects.append(image_stmt)
    if media_type in (None, "", "video"):
        selects.append(video_stmt)

    if not selects:
        return success(page_payload([], 0, page, page_size))

    task_rows = (union_all(*selects) if len(selects) > 1 else selects[0]).subquery()
    total = int((await db.execute(select(func.count()).select_from(task_rows))).scalar_one() or 0)
    result = await db.execute(
        select(task_rows)
        .order_by(task_rows.c.created_at.desc(), task_rows.c.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [_admin_task_payload(row) for row in result.mappings().all()]
    return success(page_payload(items, total, page, page_size))
