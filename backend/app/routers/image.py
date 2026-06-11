import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.image_analyzer import DashScopeConfigError, analyze_product_image
from app.core.oss import OssConfigError, upload_image_bytes
from app.models import ImageTask, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/image", tags=["生图"])

CREDITS_PER_IMAGE = 1


class GenerateRequest(BaseModel):
    prompt: str
    size: str = "720x1280"


class AnalyzeImageRequest(BaseModel):
    image_url: str
    platform: str = ""
    language: str = "中文"


@router.post("/upload", response_model=Response)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    try:
        content = await file.read()
        uploaded = await upload_image_bytes(
            user_id=current_user.id,
            content=content,
            content_type=file.content_type or "",
        )
    except (ValueError, OssConfigError) as e:
        return fail(str(e))
    except Exception:
        return fail("图片上传失败")
    finally:
        await file.close()

    return success(
        {
            "url": uploaded.url,
            "object_key": uploaded.object_key,
            "content_type": uploaded.content_type,
            "size": uploaded.size,
        }
    )


@router.post("/analyze", response_model=Response)
async def analyze_image(
    req: AnalyzeImageRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        content = await analyze_product_image(
            image_url=req.image_url,
            platform=req.platform,
            language=req.language,
        )
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        return fail("图片分析失败")

    return success({"content": content})


@router.post("/generate", response_model=Response)
async def create_task(
    req: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.credits < CREDITS_PER_IMAGE:
        return fail("积分不足")

    task_id = str(uuid.uuid4())
    current_user.credits -= CREDITS_PER_IMAGE
    await db.commit()

    task = ImageTask(
        id=task_id,
        user_id=current_user.id,
        prompt=req.prompt,
        size=req.size,
        status="pending",
    )
    db.add(task)
    await db.commit()

    await request.app.state.redis_pool.enqueue_job(
        "generate_image",
        task_id,
        req.prompt,
        req.size,
    )

    return success({"task_id": task_id})


@router.get("/task/{task_id}", response_model=Response)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ImageTask).where(
            ImageTask.id == task_id,
            ImageTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return fail("任务不存在")

    return success(
        {
            "status": task.status,
            "result_url": task.result_url,
            "prompt": task.prompt,
            "created_at": task.created_at,
        }
    )


@router.get("/tasks", response_model=Response)
async def get_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ImageTask)
        .where(ImageTask.user_id == current_user.id)
        .order_by(ImageTask.created_at.desc())
    )
    return success(result.scalars().all())