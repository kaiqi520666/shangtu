from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.models import GenerationJob, ImageTask, User
from app.schemas.response import Response, success

from .utils import image_task_payload, page_payload

router = APIRouter()


@router.get("/image-tasks", response_model=Response)
async def list_image_tasks(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    scenario: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = []
    if status in {"pending", "processing", "done", "failed", "timeout"}:
        conditions.append(ImageTask.status == status)
    if scenario in {"product_suite", "product_image", "outfit", "free_image"}:
        conditions.append(GenerationJob.scenario == scenario)
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                ImageTask.id.ilike(like),
                ImageTask.title.ilike(like),
                ImageTask.type_id.ilike(like),
                ImageTask.provider_task_id.ilike(like),
                User.email.ilike(like),
                GenerationJob.title.ilike(like),
            )
        )

    total_stmt = (
        select(func.count())
        .select_from(ImageTask)
        .join(User, User.id == ImageTask.user_id)
        .outerjoin(GenerationJob, GenerationJob.id == ImageTask.job_id)
    )
    data_stmt = (
        select(ImageTask, User, GenerationJob)
        .join(User, User.id == ImageTask.user_id)
        .outerjoin(GenerationJob, GenerationJob.id == ImageTask.job_id)
        .order_by(ImageTask.created_at.desc(), ImageTask.id.desc())
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)
    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [image_task_payload(task, user, job) for task, user, job in result.all()]
    return success(page_payload(items, total, page, page_size))
