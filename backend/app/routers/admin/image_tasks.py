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
from app.core.pagination import PaginationParams, execute_pagination, page_payload, pagination_params
from app.core.scenarios import IMAGE_SCENARIOS, VIDEO_SCENARIOS
from app.models import GenerationJob, ImageTask, User, VideoTask
from app.schemas.response import Response, success

router = APIRouter()


@router.get("/image-tasks", response_model=Response)
async def list_image_tasks(
    pagination: PaginationParams = Depends(pagination_params),
    status: str | None = None,
    scenario: str | None = None,
    media_type: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    image_stmt = image_admin_select()
    video_stmt = video_admin_select()
    if status in {"pending", "processing", "done", "failed", "timeout"}:
        image_stmt = image_stmt.where(ImageTask.status == status)
        video_stmt = video_stmt.where(VideoTask.status == status)
    if scenario in IMAGE_SCENARIOS:
        image_stmt = image_stmt.where(GenerationJob.scenario == scenario)
        video_stmt = video_stmt.where(false())
    elif scenario in VIDEO_SCENARIOS:
        image_stmt = image_stmt.where(false())
        video_stmt = video_stmt.where(VideoTask.scenario == scenario)
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
        return success(page_payload([], 0, pagination.page, pagination.page_size))

    task_rows = (union_all(*selects) if len(selects) > 1 else selects[0]).subquery()
    total, result = await execute_pagination(
        db,
        count_statement=select(func.count()).select_from(task_rows),
        data_statement=select(task_rows).order_by(
            task_rows.c.created_at.desc(), task_rows.c.id.desc()
        ),
        pagination=pagination,
    )
    items = [admin_task_payload(row) for row in result.mappings().all()]
    return success(page_payload(items, total, pagination.page, pagination.page_size))
