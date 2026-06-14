import json
import uuid

import httpx
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.image_analyzer import (
    DashScopeConfigError,
    analyze_product_image,
    generate_product_image_strategy,
)
from app.core.image_prompt_builder import (
    build_ai_write_prompt,
    build_image_generate_prompt,
    build_product_image_strategy_template_prompt,
    compose_image_prompt,
)
from app.core.oss import OssConfigError, upload_image_bytes
from app.core.time import to_utc_iso, utc_now
from app.models import GenerationJob, ImageTask, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/image", tags=["生图"])

CREDITS_PER_IMAGE = 1


class GenerateRequest(BaseModel):
    prompt: str
    user_prompt: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    ratio: str = "1:1"
    resolution: str = "1K"
    job_id: str | None = None
    type_id: str | None = None
    title: str | None = None
    sort_order: int = 0


class AnalyzeImageRequest(BaseModel):
    image_url: str
    platform: str = ""
    scenario: str | None = None


class ProductImageStrategyRequest(BaseModel):
    image_url: str
    platform: str = ""
    language: str = "中文"
    product_input: str
    module_ids: list[str]


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
    db: AsyncSession = Depends(get_db),
):
    try:
        template_prompt = await build_ai_write_prompt(
            db,
            scenario=req.scenario or "product_suite",
            platform=req.platform,
        )
        content = await analyze_product_image(
            image_url=req.image_url,
            platform=req.platform,
            prompt=template_prompt or None,
        )
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        return fail("图片分析失败")

    return success({"content": content})


@router.post("/product-image/strategy", response_model=Response)
async def product_image_strategy(
    req: ProductImageStrategyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        template_prompt = await build_product_image_strategy_template_prompt(
            db,
            platform=req.platform,
        )
        strategy = await generate_product_image_strategy(
            image_url=req.image_url,
            platform=req.platform,
            language=req.language,
            product_input=req.product_input,
            module_ids=req.module_ids,
            template_prompt=template_prompt,
        )
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        return fail("详情页策略生成失败")

    return success(strategy)


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
        if job.scenario not in {"product_suite", "product_image", "outfit"}:
            return fail("任务类型不匹配")

    task_id = str(uuid.uuid4())
    final_prompt = req.prompt
    user_prompt = req.user_prompt
    system_prompt_snapshot = None
    task_prompt_snapshot = None
    prompt_template_refs_json = None
    prepend_reference_prompt = True

    if job is not None and job.scenario in {"product_suite", "product_image", "outfit"}:
        try:
            built_prompt = await build_image_generate_prompt(
                db,
                job=job,
                type_id=req.type_id,
                title=req.title,
                user_prompt=req.user_prompt or req.prompt,
            )
        except ValueError as exc:
            return fail(str(exc))
        final_prompt = built_prompt.final_prompt
        user_prompt = built_prompt.user_prompt
        system_prompt_snapshot = built_prompt.system_prompt_snapshot
        task_prompt_snapshot = built_prompt.task_prompt_snapshot
        prompt_template_refs_json = built_prompt.prompt_template_refs_json
        prepend_reference_prompt = False

    # 扣积分 + 建任务同一事务，避免一致性漂移
    current_user.credits -= CREDITS_PER_IMAGE
    task = ImageTask(
        id=task_id,
        user_id=current_user.id,
        prompt=final_prompt,
        size=f"{req.ratio}/{req.resolution}",
        status="pending",
        job_id=req.job_id,
        type_id=req.type_id,
        title=req.title,
        sort_order=req.sort_order,
        system_prompt_snapshot=system_prompt_snapshot,
        task_prompt_snapshot=task_prompt_snapshot,
        user_prompt=user_prompt,
        prompt_template_refs_json=prompt_template_refs_json,
    )
    db.add(task)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("任务创建失败，请稍后重试")

    reference_image_urls = [url for url in (req.image_urls or []) if url]

    # 入队失败：标记任务 failed 并退回积分，避免用户被扣却没活
    try:
        await request.app.state.redis_pool.enqueue_job(
            "generate_image",
            task_id,
            final_prompt,
            req.ratio,
            req.resolution,
            prepend_reference_prompt,
            reference_image_urls,
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
            live_status_str: str | None = None
            if live_status:
                live_status_str = live_status.decode() if isinstance(live_status, bytes) else live_status
                # 防止 Redis 残留的旧 done 覆盖 DB 的 pending/processing
                if task.status in ("pending", "processing"):
                    if live_status_str != "done":
                        status = live_status_str
                    # live_status_str == "done" 时，下面会尝试取 Redis result 验证
                else:
                    status = live_status_str

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

            # 读取 Redis result —— 无论 DB result_url 是否有值都要尝试
            # 重新生成场景下 DB result_url 是旧图，需要用 Redis 的新 result 覆盖
            live_result = await redis_pool.get(f"task:{task_id}:result")
            if live_result:
                raw = live_result.decode() if isinstance(live_result, bytes) else live_result
                try:
                    parsed = json.loads(raw)
                    redis_result_url = parsed.get("url") or None
                    if redis_result_url:
                        result_url = redis_result_url
                except (TypeError, ValueError):
                    pass

            # 如果 Redis 报告 done 且 DB 还是 pending/processing，需要验证有新 result
            if live_status_str == "done" and task.status in ("pending", "processing"):
                # 只有拿到了本轮新 result 才认可 done
                if live_result:
                    try:
                        parsed = json.loads(
                            live_result.decode() if isinstance(live_result, bytes) else live_result
                        )
                        if parsed.get("url"):
                            status = "done"
                        else:
                            status = "processing"
                    except (TypeError, ValueError):
                        status = "processing"
                else:
                    status = "processing"
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
            "system_prompt_snapshot": task.system_prompt_snapshot,
            "task_prompt_snapshot": task.task_prompt_snapshot,
            "user_prompt": task.user_prompt,
            "prompt_template_refs": (
                json.loads(task.prompt_template_refs_json)
                if task.prompt_template_refs_json
                else []
            ),
            "created_at": to_utc_iso(task.created_at),
            "error_message": error_message,
            "progress": progress,
        }
    )


@router.get("/task/{task_id}/download")
async def download_task_image(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """代理下载图片，绕过浏览器跨域限制。"""
    result = await db.execute(
        select(ImageTask).where(
            ImageTask.id == task_id,
            ImageTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task or not task.result_url:
        return fail("图片不存在或尚未生成完成")

    async def stream():
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream("GET", task.result_url) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk

    # 猜测 content type
    url_lower = task.result_url.lower()
    if url_lower.endswith(".jpg") or url_lower.endswith(".jpeg"):
        media_type = "image/jpeg"
        ext = "jpg"
    elif url_lower.endswith(".webp"):
        media_type = "image/webp"
        ext = "webp"
    else:
        media_type = "image/png"
        ext = "png"

    filename = f"{task_id}.{ext}"
    return StreamingResponse(
        stream(),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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


@router.delete("/task/{task_id}", response_model=Response)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """软删除单张图片（仅标记 archived，不物理删除 OSS 文件）。"""
    result = await db.execute(
        select(ImageTask).where(
            ImageTask.id == task_id,
            ImageTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return fail("图片不存在")

    task.archived = True
    task.archived_at = utc_now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("删除失败，请稍后重试")

    return success({"task_id": task_id})


class RegenerateRequest(BaseModel):
    edit_instruction: str | None = None
    user_prompt: str | None = None


@router.post("/task/{task_id}/regenerate", response_model=Response)
async def regenerate_task(
    task_id: str,
    req: RegenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """基于已有图片重新生成。复用同一个 task_id，覆盖结果。"""
    edit_instruction = (req.edit_instruction or "").strip()
    requested_user_prompt = (req.user_prompt or "").strip()
    if not requested_user_prompt and not edit_instruction:
        return fail("请输入用户提示词")

    result = await db.execute(
        select(ImageTask).where(
            ImageTask.id == task_id,
            ImageTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        return fail("图片不存在")
    if task.archived:
        return fail("图片已被删除")
    if not task.result_url:
        return fail("该图片尚未生成完成，无法重新生成")

    if current_user.credits < CREDITS_PER_IMAGE:
        return fail("积分不足")

    # 解析原 size -> ratio/resolution
    parts = task.size.split("/") if task.size else ["1:1", "1K"]
    ratio = parts[0] if len(parts) > 0 else "1:1"
    resolution = parts[1] if len(parts) > 1 else "1K"

    # 保留旧 result_url 供前端继续展示
    old_result_url = task.result_url

    # 构造新 prompt。新模板任务优先编辑 user_prompt；旧历史任务仍兼容追加修改要求。
    has_prompt_snapshot = bool(
        task.system_prompt_snapshot
        or task.task_prompt_snapshot
        or task.prompt_template_refs_json
    )
    if has_prompt_snapshot or task.user_prompt:
        new_user_prompt = requested_user_prompt or (
            f"{task.user_prompt}\n\n【用户修改要求】{edit_instruction}"
            if task.user_prompt
            else edit_instruction
        )
        new_prompt = compose_image_prompt(
            system_prompt=task.system_prompt_snapshot,
            task_prompt=task.task_prompt_snapshot,
            user_prompt=new_user_prompt,
        )
    else:
        new_user_prompt = None
        new_prompt = task.prompt + "\n\n【用户修改要求】" + edit_instruction
    prepend_reference_prompt = not has_prompt_snapshot

    # 扣积分 + 更新 task 同一事务
    current_user.credits -= CREDITS_PER_IMAGE
    task.status = "pending"
    task.error_message = None
    task.progress = 0
    task.edit_instruction = edit_instruction or None
    task.prompt = new_prompt
    task.user_prompt = new_user_prompt
    # 保留 result_url 不清空，前端继续显示旧图
    task.credit_refunded = False
    task.provider_task_id = None

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("重新生成失败，请稍后重试")

    # 重置 Redis 运行态，避免前端轮询读到上一轮的 done/result
    # 入队 worker
    # TODO: 后续用 generation_attempts 做严格幂等退款
    try:
        redis = request.app.state.redis_pool
        await redis.delete(f"task:{task_id}:result")
        await redis.delete(f"task:{task_id}:error")
        await redis.set(f"task:{task_id}:status", "pending", ex=7200)
        await redis.set(f"task:{task_id}:progress", "0", ex=7200)

        await redis.enqueue_job(
            "generate_image",
            task_id,
            new_prompt,
            ratio,
            resolution,
            prepend_reference_prompt,
            [old_result_url],  # 使用当前已生成图作为参考图
        )
    except Exception:
        # 入队失败：退积分 + 标记 failed
        try:
            current_user.credits += CREDITS_PER_IMAGE
            task.status = "failed"
            task.error_message = "任务入队失败"
            task.credit_refunded = True
            # 恢复旧 result_url 确保前端仍可展示
            task.result_url = old_result_url
            await db.commit()
        except Exception:
            await db.rollback()
        return fail("任务入队失败，请稍后重试")

    return success({"task_id": task_id})
