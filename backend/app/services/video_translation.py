import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import dump_json_or_none
from app.core.media_projection import video_task_payload
from app.core.system_settings import get_effective_video_translation_credit_costs
from app.core.time import utc_now
from app.core.user_credits import get_user_credits, refund_user_credits
from app.models import HeygenTranslationLanguage, VideoTask
from app.schemas.response import Response, fail, success
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate
from app.services.heygen_task_lifecycle import (
    clean_text,
    get_or_create_video_job,
    normalize_duration_seconds,
    sync_video_job_status,
)

SCENARIO = "video_translation"
QUALITY_TIER_TO_MODE = {
    "standard": "speed",
    "premium": "precision",
}


def language_payload(item: HeygenTranslationLanguage) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "display_name_zh": item.display_name_zh,
        "provider": item.provider,
        "sort_order": item.sort_order,
    }


async def list_enabled_languages(db: AsyncSession) -> list[HeygenTranslationLanguage]:
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
    return list(result.scalars().all())


async def get_enabled_language(
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


def _consume_note(*, quality_tier: str, title: str | None) -> str:
    quality_label = "高质翻译" if quality_tier == "premium" else "标准翻译"
    title_text = clean_text(title)
    return f"视频翻译 · {quality_label}" + (f" · {title_text}" if title_text else "")


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
        "scenario": SCENARIO,
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


async def create_task(
    db: AsyncSession,
    *,
    user_id: int,
    get_redis_pool: Callable[[], Any],
    video_url: str,
    duration_seconds: float,
    target_language_id: str,
    quality_tier: str,
    source: str,
    asset_task_id: str | None,
    job_id: str | None,
    requested_title: str | None,
) -> Response:
    video_url = clean_text(video_url)
    if not video_url:
        return fail("请先选择视频")
    normalized_duration = normalize_duration_seconds(duration_seconds)
    if normalized_duration < 1:
        return fail("无法获取视频时长，请重新上传或选择视频")
    source = clean_text(source) or "upload"
    if source not in {"upload", "asset"}:
        return fail("视频来源不正确")
    quality_tier = clean_text(quality_tier) or "standard"
    if quality_tier not in QUALITY_TIER_TO_MODE:
        return fail("不支持的翻译档位")

    language = await get_enabled_language(db, target_language_id)
    if not language:
        return fail("目标语言不存在或已停用")
    try:
        costs = await get_effective_video_translation_credit_costs(db)
    except ValueError as exc:
        return fail(str(exc))

    per_second_cost = int(costs[quality_tier])
    base_credit_cost = per_second_cost * normalized_duration
    title = clean_text(requested_title) or f"视频翻译_{utc_now():%Y%m%d_%H%M%S}"
    settings_snapshot = _build_settings_snapshot(
        video_url=video_url,
        target_language=language,
        quality_tier=quality_tier,
        duration_seconds=normalized_duration,
        per_second_cost=per_second_cost,
        credit_cost=base_credit_cost,
        source=source,
        asset_task_id=asset_task_id,
    )
    job = await get_or_create_video_job(
        db,
        user_id=user_id,
        job_id=job_id,
        scenario=SCENARIO,
        title=title,
        settings_snapshot=settings_snapshot,
    )
    if not job:
        return fail("任务不存在")

    charge, failure = await deduct_credits_or_fail(
        db,
        user_id,
        base_credit_cost,
        note=_consume_note(quality_tier=quality_tier, title=title),
    )
    if failure is not None:
        return failure

    task = VideoTask(
        id=str(uuid.uuid4()),
        user_id=user_id,
        job_id=job.id,
        scenario=SCENARIO,
        type_id=quality_tier,
        title=title,
        sort_order=0,
        prompt="视频翻译",
        input_mode=SCENARIO,
        input_video_url=video_url,
        duration=normalized_duration,
        resolution="translation",
        aspect_ratio="original",
        status="pending",
        progress=10,
        provider="heygen",
        credit_cost=charge.cost,
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

    async def mark_failed(_refunded_credits: int) -> None:
        await db.execute(
            update(VideoTask)
            .where(VideoTask.id == task.id)
            .values(status="failed", progress=0, credit_refunded=True)
        )

    enqueue_failure = await enqueue_or_compensate(
        get_redis_pool=get_redis_pool,
        db=db,
        job_name="submit_video_translation_task",
        job_args=(task.id,),
        user_id=user_id,
        credit_cost=charge.cost,
        remaining_credits=charge.balance_after,
        refund_credits=refund_user_credits,
        mark_failed=mark_failed,
        failure_message="视频翻译任务入队失败，请稍后重试",
        failure_data={"task_id": task.id, "job_id": task.job_id},
        refund_note=f"视频翻译任务入队失败退回 · {task.id}",
    )
    if enqueue_failure is not None:
        return enqueue_failure

    return success(
        {
            "task_id": task.id,
            "job_id": task.job_id,
            "provider_task_id": None,
            "status": "pending",
            "credits": charge.balance_after,
            "credit_cost": charge.cost,
        }
    )


async def get_task(db: AsyncSession, *, task_id: str, user_id: int) -> VideoTask | None:
    result = await db.execute(
        select(VideoTask).where(
            VideoTask.id == task_id,
            VideoTask.user_id == user_id,
            VideoTask.scenario == SCENARIO,
        )
    )
    return result.scalar_one_or_none()


def task_payload(task: VideoTask) -> dict:
    payload = video_task_payload(task)
    payload["job_id"] = task.job_id
    payload["credits"] = None
    return payload


async def get_task_details(
    db: AsyncSession,
    *,
    task_id: str,
    user_id: int,
) -> dict | None:
    task = await get_task(db, task_id=task_id, user_id=user_id)
    if not task:
        return None
    payload = task_payload(task)
    payload["credits"] = await get_user_credits(db, user_id)
    return payload


async def archive_task(
    db: AsyncSession,
    *,
    task_id: str,
    user_id: int,
) -> str | None:
    task = await get_task(db, task_id=task_id, user_id=user_id)
    if not task:
        return "视频翻译任务不存在"

    task.archived = True
    task.archived_at = utc_now()
    await sync_video_job_status(db, job_id=task.job_id, scenario=SCENARIO)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return "删除失败，请稍后重试"
    return None
