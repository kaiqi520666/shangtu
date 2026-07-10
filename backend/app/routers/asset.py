from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import delete, func, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.media_download import remote_media_download_response
from app.core.media_projection import (
    audio_asset_select,
    image_asset_select,
    includes_audio,
    includes_image,
    includes_video,
    video_asset_select,
)
from app.core.oss import image_url_variants
from app.core.scenarios import SUPPORTED_GENERATION_SCENARIOS
from app.core.task_state import task_state_keys
from app.core.time import to_utc_iso
from app.models import ImageTask, User, UserAudioAsset, VideoTask
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/asset", tags=["资产库"])

SCENARIO_FILTER = SUPPORTED_GENERATION_SCENARIOS
PAGE_SIZE_MAX = 50


@router.get("/list", response_model=Response)
async def list_assets(
    scenario: str | None = Query(None, description="按场景筛选"),
    media_type: str | None = Query(None, description="按媒体类型筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=PAGE_SIZE_MAX),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if scenario:
        if scenario not in SCENARIO_FILTER:
            return fail(f"不支持的场景类型：{scenario}")

    start = (page - 1) * page_size
    selects = [
        stmt
        for stmt in (
            image_asset_select(current_user.id, scenario) if includes_image(media_type) else None,
            video_asset_select(current_user.id, scenario) if includes_video(media_type) else None,
            audio_asset_select(current_user.id, scenario) if includes_audio(media_type) else None,
        )
        if stmt is not None
    ]
    if not selects:
        return success({
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
        })

    asset_rows = (union_all(*selects) if len(selects) > 1 else selects[0]).subquery()
    total = int((await db.execute(select(func.count()).select_from(asset_rows))).scalar_one() or 0)
    result = await db.execute(
        select(asset_rows)
        .order_by(asset_rows.c.created_at.desc())
        .offset(start)
        .limit(page_size)
    )
    items = []
    for row in result.mappings().all():
        item = {
            "task_id": row["task_id"],
            "media_type": row["media_type"],
            "result_url": row["result_url"],
            "title": row["title"] or "",
            "type_id": row["type_id"] or "",
            "scenario": row["scenario"] or "",
            "job_title": row["job_title"] or "",
            "created_at": to_utc_iso(row["created_at"]),
            "source": row["source"],
            "duration_seconds": row["duration_seconds"],
            "size": row["size"],
            "content_type": row["content_type"],
        }
        if row["media_type"] == "image":
            item.update(image_url_variants(row["result_url"]))
        items.append(item)

    return success({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/{media_type}/{asset_id}/download")
async def download_asset(
    media_type: str,
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if media_type == "image":
        result = await db.execute(
            select(ImageTask).where(
                ImageTask.id == asset_id,
                ImageTask.user_id == current_user.id,
                ImageTask.status == "done",
                ImageTask.archived.is_(False),
            )
        )
        asset = result.scalar_one_or_none()
        url = asset.result_url if asset else ""
        fallback_extension = "png"
    elif media_type == "video":
        result = await db.execute(
            select(VideoTask).where(
                VideoTask.id == asset_id,
                VideoTask.user_id == current_user.id,
                VideoTask.status == "done",
                VideoTask.archived.is_(False),
            )
        )
        asset = result.scalar_one_or_none()
        url = asset.result_url if asset else ""
        fallback_extension = "mp4"
    elif media_type == "audio":
        result = await db.execute(
            select(UserAudioAsset).where(
                UserAudioAsset.id == asset_id,
                UserAudioAsset.user_id == current_user.id,
                UserAudioAsset.enabled.is_(True),
                UserAudioAsset.archived_at.is_(None),
            )
        )
        asset = result.scalar_one_or_none()
        url = asset.audio_url if asset else ""
        fallback_extension = {
            "audio/aac": "aac",
            "audio/flac": "flac",
            "audio/mp4": "m4a",
            "audio/mpeg": "mp3",
            "audio/ogg": "ogg",
            "audio/wav": "wav",
            "audio/webm": "webm",
            "audio/x-wav": "wav",
        }.get(asset.content_type if asset else "", "mp3")
    else:
        return fail("不支持的资产类型")

    if not url:
        return fail("资产不存在或不可下载")
    return remote_media_download_response(
        url,
        filename_stem=asset_id,
        fallback_extension=fallback_extension,
        media_type_override=asset.content_type if media_type == "audio" else None,
    )


class BatchDeleteRequest(BaseModel):
    task_ids: list[str]
    media_type: str | None = None


@router.delete("/batch", response_model=Response)
async def batch_delete_assets(
    req: BatchDeleteRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not req.task_ids:
        return fail("请选择要删除的资产")
    if len(req.task_ids) > 50:
        return fail("单次最多删除 50 个资产")

    deleted_ids: list[str] = []
    deleted_video_ids: list[str] = []
    if includes_image(req.media_type):
        stmt = (
            delete(ImageTask)
            .where(
                ImageTask.id.in_(req.task_ids),
                ImageTask.user_id == current_user.id,
                ImageTask.status == "done",
            )
            .returning(ImageTask.id)
        )
        result = await db.execute(stmt)
        deleted_ids.extend([row[0] for row in result.all()])
    if includes_video(req.media_type):
        stmt = (
            delete(VideoTask)
            .where(
                VideoTask.id.in_(req.task_ids),
                VideoTask.user_id == current_user.id,
                VideoTask.status == "done",
            )
            .returning(VideoTask.id)
        )
        result = await db.execute(stmt)
        deleted_video_ids.extend([row[0] for row in result.all()])
    deleted_audio_ids: list[str] = []
    if includes_audio(req.media_type):
        stmt = (
            delete(UserAudioAsset)
            .where(
                UserAudioAsset.id.in_(req.task_ids),
                UserAudioAsset.user_id == current_user.id,
            )
            .returning(UserAudioAsset.id)
        )
        result = await db.execute(stmt)
        deleted_audio_ids.extend([row[0] for row in result.all()])
    await db.commit()

    # 清理 Redis 缓存 key（best effort）
    if deleted_ids or deleted_video_ids:
        try:
            redis = request.app.state.redis_pool
            keys_to_del = []
            for task_id in deleted_ids:
                keys_to_del.extend(task_state_keys("image", task_id))
            for task_id in deleted_video_ids:
                keys_to_del.extend(task_state_keys("video", task_id))
            if keys_to_del:
                await redis.delete(*keys_to_del)
        except Exception:
            pass  # Redis 清理失败不影响主流程

    all_deleted_ids = [*deleted_ids, *deleted_video_ids, *deleted_audio_ids]
    return success({"deleted": len(all_deleted_ids), "deleted_ids": all_deleted_ids})
