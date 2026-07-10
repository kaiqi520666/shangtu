from __future__ import annotations

import uuid

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.json_utils import dump_json_or_none, parse_json_or_none
from app.core.media_projection import video_task_payload
from app.core.providers.heygen_provider import (
    parse_heygen_error_message,
)
from app.core.system_settings import get_effective_video_translation_credit_costs
from app.core.task_timeout import project_task_runtime_state
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import get_user_credits, refund_user_credits
from app.models import GenerationJob, HeygenTranslationLanguage, User, VideoTask
from app.schemas.response import Response, fail, success
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate
from app.services.heygen_task_lifecycle import (
    clean_text as _clean_text,
    get_or_create_video_job,
    normalize_duration_seconds as _normalize_duration_seconds,
    sync_video_job_status,
)

router = APIRouter(prefix="/video-translation", tags=["视频翻译"])

QUALITY_TIER_TO_MODE = {
    "standard": "speed",
    "premium": "precision",
}


class CreateVideoTranslationTaskRequest(BaseModel):
    video_url: str
    duration_seconds: float
    target_language_id: str
    quality_tier: str = "standard"
    source: str = "upload"
    asset_task_id: str | None = None
    job_id: str | None = None
    title: str | None = None


def _translation_consume_note(*, quality_tier: str, title: str | None) -> str:
    quality_label = "高质翻译" if quality_tier == "premium" else "标准翻译"
    title_text = _clean_text(title)
    return f"视频翻译 · {quality_label}" + (f" · {title_text}" if title_text else "")


def _translation_language_payload(item: HeygenTranslationLanguage) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "display_name_zh": item.display_name_zh,
        "provider": item.provider,
        "sort_order": item.sort_order,
    }


def _build_settings_snapshot(
    *,
    video_url: str,
    target_language: HeygenTranslationLanguage,
    quality_tier: str,
    duration_seconds: int,
    per_second_cost: int,
    credit_cost: int,
    source: str,
    asset_task_id: str | None,
) -> dict:
    return {
        "scenario": "video_translation",
        "media_type": "video",
        "language": target_language.name,
        "ratio": "original",
        "quality": quality_tier,
        "scene": {
            "videoUrl": video_url,
            "targetLanguageId": target_language.id,
            "targetLanguageName": target_language.name,
            "targetLanguageDisplayNameZh": target_language.display_name_zh,
            "qualityTier": quality_tier,
            "durationSeconds": duration_seconds,
            "perSecondCost": per_second_cost,
            "creditCost": credit_cost,
            "source": source,
            "assetTaskId": asset_task_id or "",
        },
    }


async def _get_enabled_language(
    db: AsyncSession,
    language_id: str,
) -> HeygenTranslationLanguage | None:
    result = await db.execute(
        select(HeygenTranslationLanguage).where(
            HeygenTranslationLanguage.id == language_id,
            HeygenTranslationLanguage.enabled == True,  # noqa: E712
            HeygenTranslationLanguage.archived_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def _get_or_create_job(
    db: AsyncSession,
    *,
    current_user: User,
    job_id: str | None,
    title: str,
    settings_snapshot: dict,
) -> GenerationJob | None:
    return await get_or_create_video_job(
        db,
        user_id=current_user.id,
        job_id=job_id,
        scenario="video_translation",
        title=title,
        settings_snapshot=settings_snapshot,
    )


async def _sync_job_status(db: AsyncSession, job_id: str | None) -> None:
    await sync_video_job_status(db, job_id=job_id, scenario="video_translation")


async def _get_task(db: AsyncSession, *, task_id: str, user_id: int) -> VideoTask | None:
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == task_id,
            VideoTask.user_id == user_id,
            VideoTask.scenario == "video_translation",
        )
    )
    return result.scalar_one_or_none()


def _task_payload(task: VideoTask) -> dict:
    payload = video_task_payload(task)
    payload["job_id"] = task.job_id
    payload["credits"] = None
    return payload


@router.get("/languages", response_model=Response)
async def list_video_translation_languages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user
    result = await db.execute(
        select(HeygenTranslationLanguage)
        .where(
            HeygenTranslationLanguage.enabled == True,  # noqa: E712
            HeygenTranslationLanguage.archived_at.is_(None),
        )
        .order_by(
            HeygenTranslationLanguage.sort_order.asc(),
            HeygenTranslationLanguage.updated_at.desc(),
            HeygenTranslationLanguage.id.desc(),
        )
    )
    return success([_translation_language_payload(item) for item in result.scalars().all()])


@router.get("/config", response_model=Response)
async def get_video_translation_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        credit_costs = await get_effective_video_translation_credit_costs(db)
    except ValueError as exc:
        return fail(str(exc))
    result = await db.execute(
        select(HeygenTranslationLanguage)
        .where(
            HeygenTranslationLanguage.enabled == True,  # noqa: E712
            HeygenTranslationLanguage.archived_at.is_(None),
        )
        .order_by(HeygenTranslationLanguage.sort_order.asc(), HeygenTranslationLanguage.id.desc())
    )
    return success(
        {
            "languages": [_translation_language_payload(item) for item in result.scalars().all()],
            "credit_costs": credit_costs,
            "credits": current_user.credits,
        }
    )


@router.post("/tasks", response_model=Response)
async def create_video_translation_task(
    req: CreateVideoTranslationTaskRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video_url = _clean_text(req.video_url)
    if not video_url:
        return fail("请先选择视频")
    duration_seconds = _normalize_duration_seconds(req.duration_seconds)
    if duration_seconds < 1:
        return fail("无法获取视频时长，请重新上传或选择视频")
    source = _clean_text(req.source) or "upload"
    if source not in {"upload", "asset"}:
        return fail("视频来源不正确")
    quality_tier = _clean_text(req.quality_tier) or "standard"
    mode = QUALITY_TIER_TO_MODE.get(quality_tier)
    if not mode:
        return fail("不支持的翻译档位")
    language = await _get_enabled_language(db, req.target_language_id)
    if not language:
        return fail("目标语言不存在或已停用")

    try:
        costs = await get_effective_video_translation_credit_costs(db)
    except ValueError as exc:
        return fail(str(exc))
    per_second_cost = int(costs[quality_tier])
    credit_cost = per_second_cost * duration_seconds
    title = _clean_text(req.title) or f"视频翻译_{utc_now():%Y%m%d_%H%M%S}"
    settings_snapshot = _build_settings_snapshot(
        video_url=video_url,
        target_language=language,
        quality_tier=quality_tier,
        duration_seconds=duration_seconds,
        per_second_cost=per_second_cost,
        credit_cost=credit_cost,
        source=source,
        asset_task_id=req.asset_task_id,
    )

    job = await _get_or_create_job(
        db,
        current_user=current_user,
        job_id=req.job_id,
        title=title,
        settings_snapshot=settings_snapshot,
    )
    if not job:
        return fail("任务不存在")

    remaining_credits, fail_response = await deduct_credits_or_fail(
        db,
        current_user.id,
        credit_cost,
        note=_translation_consume_note(quality_tier=quality_tier, title=title),
    )
    if fail_response is not None:
        return fail_response

    task = VideoTask(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        job_id=job.id,
        scenario="video_translation",
        type_id=quality_tier,
        title=title,
        sort_order=0,
        prompt="视频翻译",
        input_mode="video_translation",
        input_video_url=video_url,
        duration=duration_seconds,
        resolution="translation",
        aspect_ratio="original",
        status="pending",
        progress=10,
        provider="heygen",
        credit_cost=credit_cost,
        settings_snapshot_json=dump_json_or_none(settings_snapshot),
    )
    db.add(task)
    job.status = "generating"
    job.updated_at = utc_now()

    try:
        await db.commit()
        await db.refresh(task)
    except Exception:
        await db.rollback()
        return fail("视频翻译任务创建失败，请稍后重试")

    async def mark_task_failed(_refunded_credits: int) -> None:
        await db.execute(
            update(VideoTask)
            .where(VideoTask.id == task.id)
            .values(status="failed", progress=0, credit_refunded=True)
        )

    enqueue_fail = await enqueue_or_compensate(
        get_redis_pool=lambda: request.app.state.redis_pool,
        db=db,
        job_name="submit_video_translation_task",
        job_args=(task.id,),
        user_id=current_user.id,
        credit_cost=credit_cost,
        remaining_credits=remaining_credits,
        refund_credits=refund_user_credits,
        mark_failed=mark_task_failed,
        failure_message="视频翻译任务入队失败，请稍后重试",
        failure_data={"task_id": task.id, "job_id": task.job_id},
        refund_note=f"视频翻译任务入队失败退回 · {task.id}",
    )
    if enqueue_fail is not None:
        return enqueue_fail

    return success(
        {
            "task_id": task.id,
            "job_id": task.job_id,
            "provider_task_id": None,
            "status": "pending",
            "credits": remaining_credits,
            "credit_cost": credit_cost,
        }
    )


@router.get("/tasks/{task_id}", response_model=Response)
async def get_video_translation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("视频翻译任务不存在")
    payload = _task_payload(task)
    payload["credits"] = await get_user_credits(db, current_user.id)
    return success(payload)


@router.get("/tasks/{task_id}/poll", response_model=Response)
async def poll_video_translation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("视频翻译任务不存在")
    payload = _task_payload(task)
    payload["credits"] = await get_user_credits(db, current_user.id)
    return success(payload)


@router.delete("/tasks/{task_id}", response_model=Response)
async def delete_video_translation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        return fail("视频翻译任务不存在")
    task.archived = True
    task.archived_at = utc_now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return fail("删除失败，请稍后重试")
    return success({"task_id": task_id})


@router.get("/tasks/{task_id}/download")
async def download_video_translation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task(db, task_id=task_id, user_id=current_user.id)
    if not task or not task.result_url:
        return fail("视频不存在或尚未生成完成")

    async def stream():
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("GET", task.result_url) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk

    return StreamingResponse(
        stream(),
        media_type="video/mp4",
        headers={"Content-Disposition": f'attachment; filename="{task_id}.mp4"'},
    )
