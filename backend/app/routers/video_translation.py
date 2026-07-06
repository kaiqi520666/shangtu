from __future__ import annotations

import math
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.json_utils import dump_json_or_none, parse_json_or_none
from app.core.media_projection import video_task_payload
from app.core.providers.heygen_provider import (
    create_video_translation,
    get_video_translation,
    parse_heygen_error_message,
)
from app.core.system_settings import get_effective_video_translation_credit_costs
from app.core.task_timeout import project_task_runtime_state
from app.core.time import to_utc_iso, utc_now
from app.core.user_credits import get_user_credits, refund_user_credits
from app.models import GenerationJob, HeygenTranslationLanguage, User, VideoTask
from app.schemas.response import Response, fail, success
from app.services.generation_tasks import deduct_credits_or_fail

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


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_duration_seconds(value: float | int | None) -> int:
    try:
        duration = math.ceil(float(value or 0))
    except (TypeError, ValueError):
        return 0
    return max(0, duration)


def _translation_consume_note(*, quality_tier: str, title: str | None) -> str:
    quality_label = "高质翻译" if quality_tier == "premium" else "标准翻译"
    title_text = _clean_text(title)
    return f"视频翻译 · {quality_label}" + (f" · {title_text}" if title_text else "")


def _task_status_from_provider(
    provider_status: str | None,
    *,
    video_url: str | None = None,
    failure_message: str | None = None,
) -> str:
    normalized = _clean_text(provider_status).lower()
    if video_url:
        return "done"
    if normalized in {"completed", "done", "success", "succeeded"}:
        return "done"
    if normalized in {"failed", "error", "canceled", "cancelled"} or failure_message:
        return "failed"
    if normalized in {"pending", "queued", "processing", "rendering", "in_progress"}:
        return "processing" if normalized != "pending" else "pending"
    return "processing"


def _task_progress_from_status(status: str) -> int:
    if status == "done":
        return 100
    if status == "failed":
        return 0
    if status == "processing":
        return 65
    return 10


def _first_string(data: Any, keys: set[str]) -> str:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys:
                text = _clean_text(value)
                if text:
                    return text
            nested = _first_string(value, keys)
            if nested:
                return nested
    if isinstance(data, list):
        for item in data:
            nested = _first_string(item, keys)
            if nested:
                return nested
    return ""


def _extract_translation_task_id(data: dict[str, Any]) -> str:
    return _first_string(
        data,
        {
            "video_translation_id",
            "video_translate_id",
            "translation_id",
            "task_id",
            "id",
        },
    )


def _extract_result_video_url(data: dict[str, Any]) -> str:
    return _first_string(data, {"video_url", "url", "result_url", "output_url", "translated_video_url"})


def _extract_error_message(data: dict[str, Any]) -> str:
    return _first_string(data, {"error_message", "failure_reason", "message"})


def _extract_status(data: dict[str, Any]) -> str:
    return _first_string(data, {"status", "video_status", "translation_status"})


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
    if job_id:
        result = await db.execute(
            select(GenerationJob).where(
                GenerationJob.id == job_id,
                GenerationJob.user_id == current_user.id,
                GenerationJob.scenario == "video_translation",
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            return None
        job.title = title
        job.settings_json = dump_json_or_none(settings_snapshot)
        job.updated_at = utc_now()
        return job

    job = GenerationJob(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        scenario="video_translation",
        title=title,
        status="draft",
        settings_json=dump_json_or_none(settings_snapshot),
    )
    db.add(job)
    return job


async def _sync_job_status(db: AsyncSession, job_id: str | None) -> None:
    if not job_id:
        return
    job = await db.get(GenerationJob, job_id)
    if not job:
        return
    result = await db.execute(
        select(VideoTask.status, VideoTask.result_url, VideoTask.error_message, VideoTask.created_at).where(
            VideoTask.job_id == job_id,
            VideoTask.archived == False,  # noqa: E712
            VideoTask.scenario == "video_translation",
        )
    )
    rows = result.all()
    if not rows:
        job.status = "draft"
        job.updated_at = utc_now()
        return

    completed = 0
    failed = 0
    for status, result_url, error_message, created_at in rows:
        runtime = project_task_runtime_state(
            "video",
            status=status,
            error_message=error_message,
            progress=0,
            result_url=result_url,
            created_at=created_at,
        )
        if runtime.status == "done":
            completed += 1
        elif runtime.status in {"failed", "timeout"}:
            failed += 1

    if completed == len(rows):
        job.status = "done"
    elif failed == len(rows):
        job.status = "failed"
    else:
        job.status = "generating"
    job.updated_at = utc_now()


async def _refund_task_credits_if_needed(
    db: AsyncSession,
    task: VideoTask,
    *,
    note: str,
) -> int | None:
    if task.credit_refunded or int(task.credit_cost or 0) <= 0:
        return None
    refunded = await refund_user_credits(db, task.user_id, int(task.credit_cost), note=note)
    task.credit_refunded = True
    return refunded


async def _get_task(db: AsyncSession, *, task_id: str, user_id: int) -> VideoTask | None:
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == task_id,
            VideoTask.user_id == user_id,
            VideoTask.scenario == "video_translation",
        )
    )
    return result.scalar_one_or_none()


async def _sync_task_from_provider(db: AsyncSession, task: VideoTask) -> VideoTask:
    if not task.provider_task_id:
        return task

    async with httpx.AsyncClient(timeout=60) as client:
        data = await get_video_translation(
            client,
            video_translation_id=task.provider_task_id,
        )

    video_url = _extract_result_video_url(data) or None
    error_message = _extract_error_message(data) or None
    local_status = _task_status_from_provider(
        _extract_status(data),
        video_url=video_url,
        failure_message=error_message,
    )
    task.status = local_status
    task.progress = _task_progress_from_status(local_status)
    task.result_url = video_url
    task.error_message = error_message
    if local_status == "failed":
        await _refund_task_credits_if_needed(
            db,
            task,
            note=f"视频翻译失败退回 · {task.id}",
        )
    await _sync_job_status(db, task.job_id)
    await db.commit()
    await db.refresh(task)
    return task


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
        async with httpx.AsyncClient(timeout=60) as client:
            provider_data = await create_video_translation(
                client,
                video_url=video_url,
                title=title,
                output_language=language.name,
                mode=mode,
                idempotency_key=task.id,
            )
        provider_task_id = _extract_translation_task_id(provider_data)
        if not provider_task_id:
            raise ValueError("HeyGen 未返回视频翻译任务 ID")
        task.provider_task_id = provider_task_id
        task.status = _task_status_from_provider(_extract_status(provider_data))
        task.progress = _task_progress_from_status(task.status)
        await db.commit()
        await db.refresh(task)
    except ValueError as exc:
        task.status = "failed"
        task.error_message = str(exc)
        refunded = await _refund_task_credits_if_needed(
            db,
            task,
            note=f"视频翻译创建失败退回 · {task.id}",
        )
        await _sync_job_status(db, job.id)
        await db.commit()
        return fail(
            str(exc),
            data={
                "task_id": task.id,
                "credits": refunded if refunded is not None else await get_user_credits(db, current_user.id),
                "credit_cost": credit_cost,
            },
        )
    except httpx.HTTPError as exc:
        message = parse_heygen_error_message(exc)
        task.status = "failed"
        task.error_message = message
        refunded = await _refund_task_credits_if_needed(
            db,
            task,
            note=f"视频翻译创建失败退回 · {task.id}",
        )
        await _sync_job_status(db, job.id)
        await db.commit()
        return fail(
            message,
            data={
                "task_id": task.id,
                "credits": refunded if refunded is not None else await get_user_credits(db, current_user.id),
                "credit_cost": credit_cost,
            },
        )
    except Exception:
        task.status = "failed"
        task.error_message = "HeyGen 视频翻译创建失败，请稍后重试"
        refunded = await _refund_task_credits_if_needed(
            db,
            task,
            note=f"视频翻译创建失败退回 · {task.id}",
        )
        await _sync_job_status(db, job.id)
        await db.commit()
        return fail(
            "HeyGen 视频翻译创建失败，请稍后重试",
            data={
                "task_id": task.id,
                "credits": refunded if refunded is not None else await get_user_credits(db, current_user.id),
                "credit_cost": credit_cost,
            },
        )

    payload = _task_payload(task)
    payload["credits"] = remaining_credits
    return success(payload)


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
    if task.status not in {"done", "failed", "timeout"}:
        try:
            task = await _sync_task_from_provider(db, task)
        except httpx.HTTPError as exc:
            return fail(parse_heygen_error_message(exc))
        except Exception:
            return fail("HeyGen 视频翻译状态查询失败，请稍后重试")
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
