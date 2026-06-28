from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas.response import Response, success
from app.services.image_generation import (
    ImageGeneratePayload,
    ImageRegeneratePayload,
    create_image_generation_task,
    regenerate_image_generation_task,
)
from app.routers.image_catalog import router as image_catalog_router
from app.routers.image_strategy import router as image_strategy_router
from app.routers.image_tasks import router as image_tasks_router
from app.routers.image_uploads import router as image_uploads_router

router = APIRouter(prefix="/image", tags=["生图"])
router.include_router(image_catalog_router)
router.include_router(image_strategy_router)
router.include_router(image_tasks_router)
router.include_router(image_uploads_router)

class GenerateRequest(BaseModel):
    user_prompt: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    ratio: str = "1:1"
    resolution: str = "1K"
    settings_snapshot: dict | None = None
    job_id: str | None = None
    type_id: str | None = None
    title: str | None = None
    sort_order: int = 0


@router.post("/generate", response_model=Response)
async def create_image_task(
    req: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result, failure = await create_image_generation_task(
        db=db,
        current_user=current_user,
        payload=ImageGeneratePayload(
            user_prompt=req.user_prompt,
            image_urls=req.image_urls,
            ratio=req.ratio,
            resolution=req.resolution,
            settings_snapshot=req.settings_snapshot,
            job_id=req.job_id,
            type_id=req.type_id,
            title=req.title,
            sort_order=req.sort_order,
        ),
        get_redis_pool=lambda: request.app.state.redis_pool,
    )
    if failure is not None:
        return failure

    return success(
        {
            "task_id": result.task_id,
            "credits": result.credits,
            "credit_cost": result.credit_cost,
        }
    )


class RegenerateRequest(BaseModel):
    edit_instruction: str | None = None
    user_prompt: str | None = None


@router.post("/task/{task_id}/regenerate", response_model=Response)
async def regenerate_image_task(
    task_id: str,
    req: RegenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """基于已有图片重新生成。新建 ImageTask，旧任务保留为历史资产。"""
    result, failure = await regenerate_image_generation_task(
        db=db,
        current_user=current_user,
        task_id=task_id,
        payload=ImageRegeneratePayload(
            edit_instruction=req.edit_instruction,
            user_prompt=req.user_prompt,
        ),
        get_redis_pool=lambda: request.app.state.redis_pool,
    )
    if failure is not None:
        return failure

    return success(
        {
            "task_id": result.task_id,
            "source_task_id": result.source_task_id,
            "credits": result.credits,
            "credit_cost": result.credit_cost,
        }
    )
