from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.media_download import remote_media_download_response
from app.core.system_settings import get_effective_video_translation_credit_costs
from app.models import User
from app.schemas.response import Response, fail, success
from app.services.video_translation import (
    archive_task as _archive_task,
    create_task as _create_task,
    get_task as _get_task,
    get_task_details as _get_task_details,
    language_payload as _translation_language_payload,
    list_enabled_languages as _list_enabled_languages,
)

router = APIRouter(prefix="/video-translation", tags=["视频翻译"])


class CreateVideoTranslationTaskRequest(BaseModel):
    video_url: str
    duration_seconds: float
    target_language_id: str
    quality_tier: str = "standard"
    source: str = "upload"
    asset_task_id: str | None = None
    job_id: str | None = None
    title: str | None = None



@router.get("/languages", response_model=Response)
async def list_video_translation_languages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    languages = await _list_enabled_languages(db)
    return success([_translation_language_payload(item) for item in languages])


@router.get("/config", response_model=Response)
async def get_video_translation_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        credit_costs = await get_effective_video_translation_credit_costs(db)
    except ValueError as exc:
        return fail(str(exc))
    languages = await _list_enabled_languages(db)
    return success(
        {
            "languages": [_translation_language_payload(item) for item in languages],
            "credit_costs": credit_costs,
            "credits": current_user.credits,
            "consumption_multiplier": float(current_user.consumption_multiplier),
        }
    )


@router.post("/tasks", response_model=Response)
async def create_video_translation_task(
    req: CreateVideoTranslationTaskRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _create_task(
        db,
        user_id=current_user.id,
        get_redis_pool=lambda: request.app.state.redis_pool,
        video_url=req.video_url,
        duration_seconds=req.duration_seconds,
        target_language_id=req.target_language_id,
        quality_tier=req.quality_tier,
        source=req.source,
        asset_task_id=req.asset_task_id,
        job_id=req.job_id,
        requested_title=req.title,
    )


@router.get("/tasks/{task_id}", response_model=Response)
async def get_video_translation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = await _get_task_details(db, task_id=task_id, user_id=current_user.id)
    if payload is None:
        return fail("视频翻译任务不存在")
    return success(payload)


@router.get("/tasks/{task_id}/poll", response_model=Response)
async def poll_video_translation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = await _get_task_details(db, task_id=task_id, user_id=current_user.id)
    if payload is None:
        return fail("视频翻译任务不存在")
    return success(payload)


@router.delete("/tasks/{task_id}", response_model=Response)
async def delete_video_translation_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    error_message = await _archive_task(db, task_id=task_id, user_id=current_user.id)
    if error_message:
        return fail(error_message)
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

    return remote_media_download_response(
        task.result_url,
        filename_stem=task_id,
        fallback_extension="mp4",
    )
