from fastapi import APIRouter, Depends
from sqlalchemy import false, func, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.media_projection import (
    admin_task_payload,
    image_admin_select,
    includes_image,
    includes_video,
    video_admin_select,
)
from app.models import GenerationJob, ImageTask, User, VideoTask
from app.schemas.response import Response, success

from .utils import page_payload

router = APIRouter()


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
    image_stmt = image_admin_select()
    video_stmt = video_admin_select()
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
    if includes_image(media_type):
        selects.append(image_stmt)
    if includes_video(media_type):
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
    items = [admin_task_payload(row) for row in result.mappings().all()]
    return success(page_payload(items, total, page, page_size))
