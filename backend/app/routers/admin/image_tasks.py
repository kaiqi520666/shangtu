from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.models import GenerationJob, ImageTask, User, VideoTask
from app.schemas.response import Response, success

from .utils import image_task_payload, page_payload, video_task_payload

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
    image_conditions = []
    video_conditions = []
    if status in {"pending", "processing", "done", "failed", "timeout"}:
        image_conditions.append(ImageTask.status == status)
        video_conditions.append(VideoTask.status == status)
    if scenario in {"product_suite", "product_image", "outfit", "free_image"}:
        image_conditions.append(GenerationJob.scenario == scenario)
        video_conditions.append(False)
    elif scenario == "product_video":
        image_conditions.append(False)
    if keyword:
        like = f"%{keyword.strip()}%"
        image_conditions.append(
            or_(
                ImageTask.id.ilike(like),
                ImageTask.title.ilike(like),
                ImageTask.type_id.ilike(like),
                ImageTask.provider_task_id.ilike(like),
                User.email.ilike(like),
                GenerationJob.title.ilike(like),
            )
        )
        video_conditions.append(
            or_(
                VideoTask.id.ilike(like),
                VideoTask.title.ilike(like),
                VideoTask.type_id.ilike(like),
                VideoTask.provider_task_id.ilike(like),
                User.email.ilike(like),
                GenerationJob.title.ilike(like),
            )
        )

    items_with_sort = []
    if media_type in (None, "", "image"):
        data_stmt = (
            select(ImageTask, User, GenerationJob)
            .join(User, User.id == ImageTask.user_id)
            .outerjoin(GenerationJob, GenerationJob.id == ImageTask.job_id)
        )
        for condition in image_conditions:
            data_stmt = data_stmt.where(condition)
        result = await db.execute(data_stmt)
        items_with_sort.extend(
            (
                task.created_at,
                image_task_payload(task, user, job) | {"media_type": "image"},
            )
            for task, user, job in result.all()
        )
    if media_type in (None, "", "video"):
        data_stmt = (
            select(VideoTask, User, GenerationJob)
            .join(User, User.id == VideoTask.user_id)
            .outerjoin(GenerationJob, GenerationJob.id == VideoTask.job_id)
        )
        for condition in video_conditions:
            data_stmt = data_stmt.where(condition)
        result = await db.execute(data_stmt)
        items_with_sort.extend(
            (task.created_at, video_task_payload(task, user, job))
            for task, user, job in result.all()
        )

    items_with_sort.sort(key=lambda item: item[0], reverse=True)
    total = len(items_with_sort)
    items = [
        item
        for _, item in items_with_sort[(page - 1) * page_size: page * page_size]
    ]
    return success(page_payload(items, total, page, page_size))
