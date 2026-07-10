from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cosyvoice_catalog import COSYVOICE_V3_FLASH
from app.core.deps import get_current_user, get_db
from app.core.json_utils import dump_json
from app.core.media_projection import voiceover_task_payload
from app.core.system_settings import get_effective_voiceover_credit_cost
from app.core.time import utc_now
from app.core.user_credits import get_user_credits, refund_user_credits
from app.core.voiceover import (
    VOICEOVER_FORMAT,
    VOICEOVER_SAMPLE_RATE,
    VOICEOVER_TEXT_LIMIT,
    calculate_voiceover_credit_cost,
    count_voiceover_characters,
)
from app.models import CosyVoiceVoice, GenerationJob, User, UserAudioAsset, VoiceoverTask
from app.schemas.response import Response, fail, success
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate

router = APIRouter(prefix="/voiceover", tags=["AI配音"])


class CreateVoiceoverTaskRequest(BaseModel):
    job_id: str = Field(..., min_length=1, max_length=36)
    text: str = Field(..., min_length=1)
    voice_id: str = Field(..., min_length=1, max_length=128)
    rate: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    volume: int = Field(default=100, ge=0, le=100)
    instruction: str | None = Field(default=None, max_length=100)


def voice_payload(voice: CosyVoiceVoice) -> dict:
    return {
        "id": voice.id,
        "model_id": voice.model_id,
        "voice_id": voice.voice_id,
        "name": voice.name,
        "category": voice.category,
        "trait": voice.trait,
        "age_range": voice.age_range,
        "languages": voice.languages,
        "supports_instruct": voice.supports_instruct,
        "supports_timestamp": voice.supports_timestamp,
        "preview_audio_url": voice.preview_audio_url,
    }


async def get_owned_task(db: AsyncSession, task_id: str, user_id: int) -> VoiceoverTask | None:
    result = await db.execute(
        select(VoiceoverTask).where(
            VoiceoverTask.id == task_id,
            VoiceoverTask.user_id == user_id,
            VoiceoverTask.archived.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def get_task_asset(db: AsyncSession, task: VoiceoverTask) -> UserAudioAsset | None:
    return await db.get(UserAudioAsset, task.result_asset_id) if task.result_asset_id else None


@router.get("/voices", response_model=Response)
async def list_voices(
    page: int = 1,
    page_size: int = 24,
    keyword: str | None = None,
    category: str | None = None,
    language: str | None = None,
    supports_instruct: bool | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = [
        CosyVoiceVoice.model_id == COSYVOICE_V3_FLASH,
        CosyVoiceVoice.enabled.is_(True),
    ]
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                CosyVoiceVoice.name.ilike(like),
                CosyVoiceVoice.voice_id.ilike(like),
                CosyVoiceVoice.trait.ilike(like),
                CosyVoiceVoice.languages.ilike(like),
            )
        )
    if category:
        conditions.append(CosyVoiceVoice.category == category)
    if language:
        conditions.append(CosyVoiceVoice.languages.ilike(f"%{language.strip()}%"))
    if supports_instruct is not None:
        conditions.append(CosyVoiceVoice.supports_instruct == supports_instruct)

    total = int(
        (await db.execute(select(func.count()).select_from(CosyVoiceVoice).where(*conditions))).scalar_one()
        or 0
    )
    result = await db.execute(
        select(CosyVoiceVoice)
        .where(*conditions)
        .order_by(CosyVoiceVoice.sort_order, CosyVoiceVoice.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    categories = (
        await db.execute(
            select(CosyVoiceVoice.category)
            .where(CosyVoiceVoice.model_id == COSYVOICE_V3_FLASH, CosyVoiceVoice.enabled.is_(True))
            .distinct()
            .order_by(CosyVoiceVoice.category)
        )
    ).scalars().all()
    return success({"items": [voice_payload(item) for item in result.scalars().all()], "total": total, "page": page, "page_size": page_size, "categories": list(categories)})


@router.get("/config", response_model=Response)
async def get_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return success(
        {
            "text_limit": VOICEOVER_TEXT_LIMIT,
            "credit_cost_per_100_chars": await get_effective_voiceover_credit_cost(db),
            "format": VOICEOVER_FORMAT,
            "sample_rate": VOICEOVER_SAMPLE_RATE,
        }
    )


@router.post("/tasks", response_model=Response)
async def create_task(
    req: CreateVoiceoverTaskRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    text = req.text.strip()
    character_count = count_voiceover_characters(text)
    if character_count < 1:
        return fail("请输入配音文本")
    if character_count > VOICEOVER_TEXT_LIMIT:
        return fail(f"单次配音最多{VOICEOVER_TEXT_LIMIT}个非空白字符")

    job = (
        await db.execute(
            select(GenerationJob).where(
                GenerationJob.id == req.job_id,
                GenerationJob.user_id == current_user.id,
                GenerationJob.scenario == "voiceover",
                GenerationJob.archived.is_(False),
            )
        )
    ).scalar_one_or_none()
    if not job:
        return fail("AI配音任务不存在")

    voice = (
        await db.execute(
            select(CosyVoiceVoice).where(
                CosyVoiceVoice.model_id == COSYVOICE_V3_FLASH,
                CosyVoiceVoice.voice_id == req.voice_id,
                CosyVoiceVoice.enabled.is_(True),
            )
        )
    ).scalar_one_or_none()
    if not voice:
        return fail("所选音色不可用")
    instruction = (req.instruction or "").strip()
    if instruction and not voice.supports_instruct:
        return fail("所选音色不支持表达指令")

    unit_cost = await get_effective_voiceover_credit_cost(db)
    credit_cost = calculate_voiceover_credit_cost(character_count, unit_cost)
    remaining_credits, failure = await deduct_credits_or_fail(
        db, current_user.id, credit_cost, note=f"AI配音 · {voice.name}"
    )
    if failure:
        return failure

    snapshot = {
        "model": COSYVOICE_V3_FLASH,
        "voice_id": voice.voice_id,
        "voice_name": voice.name,
        "voice_trait": voice.trait,
        "voice_category": voice.category,
        "supports_instruct": voice.supports_instruct,
        "rate": req.rate,
        "pitch": req.pitch,
        "volume": req.volume,
        "instruction": instruction,
        "format": VOICEOVER_FORMAT,
        "sample_rate": VOICEOVER_SAMPLE_RATE,
        "character_count": character_count,
    }
    task = VoiceoverTask(
        user_id=current_user.id,
        job_id=job.id,
        voice_id=voice.voice_id,
        text=text,
        rate=req.rate,
        pitch=req.pitch,
        volume=req.volume,
        instruction=instruction or None,
        credit_cost=credit_cost,
        settings_snapshot_json=dump_json(snapshot),
    )
    db.add(task)
    job.status = "generating"
    job.input_text = text
    job.settings_json = dump_json(snapshot)
    await db.flush()
    await db.commit()

    async def mark_failed(_credits: int) -> None:
        task.status = "failed"
        task.error_message = "任务入队失败，请稍后重试"
        task.credit_refunded = True
        job.status = "failed"

    enqueue_failure = await enqueue_or_compensate(
        get_redis_pool=lambda: request.app.state.redis_pool,
        db=db,
        job_name="generate_voiceover",
        job_args=[task.id],
        user_id=current_user.id,
        credit_cost=credit_cost,
        remaining_credits=remaining_credits,
        refund_credits=refund_user_credits,
        mark_failed=mark_failed,
        failure_message="AI配音任务创建失败，请稍后重试",
        failure_data={"task_id": task.id},
        refund_note=f"AI配音任务入队失败退回 · {task.id}",
    )
    if enqueue_failure:
        return enqueue_failure
    return success({**voiceover_task_payload(task), "credits": remaining_credits})


@router.get("/tasks/{task_id}", response_model=Response)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_owned_task(db, task_id, current_user.id)
    if not task:
        return fail("AI配音任务不存在")
    payload = voiceover_task_payload(task, await get_task_asset(db, task))
    payload["credits"] = await get_user_credits(db, current_user.id)
    return success(payload)


@router.delete("/tasks/{task_id}", response_model=Response)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_owned_task(db, task_id, current_user.id)
    if not task:
        return fail("AI配音任务不存在")
    if task.status in {"pending", "processing"}:
        return fail("生成中的任务不能删除")
    task.archived = True
    task.archived_at = utc_now()
    asset = await get_task_asset(db, task)
    if asset:
        asset.enabled = False
        asset.archived_at = utc_now()
    await db.commit()
    return success({"task_id": task.id})
