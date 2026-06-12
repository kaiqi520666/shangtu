import json
import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.image_analyzer import DashScopeConfigError, analyze_product_image
from app.core.oss import OssConfigError, upload_image_bytes
from app.models import GenerationJob, ImageTask, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/image", tags=["生图"])

CREDITS_PER_IMAGE = 1


class GenerateRequest(BaseModel):
    prompt: str
    image_url: str | None = None
    ratio: str = "1:1"
    resolution: str = "1K"
    job_id: str | None = None
    type_id: str | None = None
    title: str | None = None
    sort_order: int = 0


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

    job: GenerationJob | None = None
    if req.job_id:
        job_result = await db.execute(
            select(GenerationJob).where(
                GenerationJob.id == req.job_id,
                GenerationJob.user_id == current_user.id,
            )
        )
        job = job_result.scalar_one_or_none()
        if not job:
            return fail("任务不存在")
        if job.scenario != "product_suite":
            return fail("任务类型不匹配")

    task_id = str(uuid.uuid4())

    # 扣积分 + 建任务同一事务，避免一致性漂移
    current_user.credits -= CREDITS_PER_IMAGE
    task = ImageTask(
        id=task_id,
        user_id=current_user.id,
        prompt=req.prompt,
        size=f"{req.ratio}/{req.resolution}",
        status="pending",
        job_id=req.job_id,
        type_id=req.type_id,
        title=req.title,
        sort_order=req.sort_order,
    )
    db.add(task)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("任务创建失败，请稍后重试")

    # 入队失败：标记任务 failed 并退回积分，避免用户被扣却没活
    try:
        await request.app.state.redis_pool.enqueue_job(
            "generate_image",
            task_id,
            req.prompt,
            req.ratio,
            req.resolution,
            req.image_url,
        )
    except Exception:
        try:
            current_user.credits += CREDITS_PER_IMAGE
            await db.execute(
                update(ImageTask)
                .where(ImageTask.id == task_id)
                .values(status="failed", credit_refunded=True)
            )
            await db.commit()
        except Exception:
            await db.rollback()
        return fail("任务入队失败，请稍后重试")

    if job is not None and job.status != "generating":
        try:
            await db.execute(
                update(GenerationJob)
                .where(GenerationJob.id == job.id)
                .values(status="generating")
            )
            await db.commit()
        except Exception:
            await db.rollback()

    return success({"task_id": task_id})


@router.get("/task/{task_id}", response_model=Response)
async def get_task(
    task_id: str,
    request: Request,
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

    status = task.status
    result_url = task.result_url
    error_message: str | None = task.error_message
    progress: int = task.progress or 0
    redis_pool = getattr(request.app.state, "redis_pool", None)
    if redis_pool is not None:
        try:
            live_status = await redis_pool.get(f"task:{task_id}:status")
            if live_status:
                status = live_status.decode() if isinstance(live_status, bytes) else live_status
            live_error = await redis_pool.get(f"task:{task_id}:error")
            if live_error:
                error_message = live_error.decode() if isinstance(live_error, bytes) else live_error
            live_progress = await redis_pool.get(f"task:{task_id}:progress")
            if live_progress:
                raw = live_progress.decode() if isinstance(live_progress, bytes) else live_progress
                try:
                    progress = max(0, min(100, int(raw)))
                except (TypeError, ValueError):
                    pass
            if not result_url:
                live_result = await redis_pool.get(f"task:{task_id}:result")
                if live_result:
                    raw = live_result.decode() if isinstance(live_result, bytes) else live_result
                    try:
                        parsed = json.loads(raw)
                        result_url = parsed.get("url") or None
                    except (TypeError, ValueError):
                        pass
        except Exception:
            pass

    # 兜底：Redis 已写入 status=done 但 DB 还没更新 result_url 时，降级为 processing，
    # 让前端继续轮询，避免出现 done + result_url=null 的不一致。
    if status == "done" and not result_url:
        status = "processing"

    if status == "done":
        progress = 100

    return success(
        {
            "status": status,
            "result_url": result_url,
            "prompt": task.prompt,
            "created_at": task.created_at,
            "error_message": error_message,
            "progress": progress,
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