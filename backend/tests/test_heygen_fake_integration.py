import asyncio
import os
import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import redis.asyncio as redis_async
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.core.json_utils import dump_json_or_none
from app.core.system_settings import get_effective_digital_human_credit_costs
from app.core.task_state import task_state_keys
from app.models import CreditTransaction, GenerationJob, User, VideoTask
from app.worker.heygen_tasks import (
    submit_digital_human_task,
    submit_video_translation_task,
)

pytestmark = [
    pytest.mark.asyncio(loop_scope="module"),
    pytest.mark.skipif(
        os.getenv("RUN_HEYGEN_FAKE_INTEGRATION") != "1",
        reason="requires local PostgreSQL and Redis",
    ),
]


async def create_case(scenario: str, *, credits: int, credit_cost: int):
    suffix = uuid.uuid4().hex
    job_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    async with SessionLocal() as db:
        user = User(
            username=f"fake_{suffix[:20]}",
            email=f"fake_{suffix}@example.test",
            password_hash="integration-test",
            credits=credits,
        )
        db.add(user)
        await db.flush()
        job = GenerationJob(
            id=job_id,
            user_id=user.id,
            scenario=scenario,
            title="Fake HeyGen integration",
            status="generating",
        )
        scene = (
            {
                "avatarId": "avatar-test",
                "audioMode": "platform",
                "voiceId": "voice-test",
                "script": "integration test",
                "voiceSettings": {"speed": 1},
            }
            if scenario == "digital_human"
            else {
                "videoUrl": "https://example.test/source.mp4",
                "targetLanguageName": "English",
            }
        )
        task = VideoTask(
            id=task_id,
            user_id=user.id,
            job_id=job_id,
            scenario=scenario,
            type_id="standard",
            title="Fake HeyGen integration",
            sort_order=0,
            prompt="integration test",
            input_mode="avatar" if scenario == "digital_human" else "video_translation",
            input_video_url=(
                None if scenario == "digital_human" else "https://example.test/source.mp4"
            ),
            duration=0,
            resolution="1080p" if scenario == "digital_human" else "translation",
            aspect_ratio="9:16" if scenario == "digital_human" else "original",
            status="pending",
            progress=10,
            provider="heygen",
            credit_cost=credit_cost,
            settings_snapshot_json=dump_json_or_none(
                {"scenario": scenario, "scene": scene}
            ),
        )
        db.add_all([job, task])
        await db.commit()
        return user.id, job_id, task_id


async def cleanup_case(redis_client, user_id: int, job_id: str, task_id: str):
    await redis_client.delete(*task_state_keys("video", task_id))
    async with SessionLocal() as db:
        await db.execute(delete(CreditTransaction).where(CreditTransaction.user_id == user_id))
        await db.execute(delete(VideoTask).where(VideoTask.id == task_id))
        await db.execute(delete(GenerationJob).where(GenerationJob.id == job_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()


async def test_digital_human_transient_retry_and_duplicate_execution_are_idempotent():
    redis_client = redis_async.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )
    async with SessionLocal() as db:
        per_second = (await get_effective_digital_human_credit_costs(db))["standard"]
    duration = 2
    user_id, job_id, task_id = await create_case(
        "digital_human", credits=100, credit_cost=per_second * duration
    )
    create_fake = AsyncMock(
        side_effect=[
            httpx.ConnectError("temporary-1"),
            httpx.ConnectError("temporary-2"),
            {"video_id": "fake-video-1", "status": "pending"},
        ]
    )
    poll_fake = AsyncMock(
        side_effect=[
            asyncio.CancelledError(),
            {
                "status": "completed",
                "video_url": "https://example.test/result.mp4",
                "duration": duration,
            },
        ]
    )
    try:
        with (
            patch("app.worker.heygen_tasks.create_avatar_video", create_fake),
            patch("app.worker.heygen_tasks.get_video", poll_fake),
            patch("app.worker.heygen_tasks.asyncio.sleep", AsyncMock()),
        ):
            with pytest.raises(asyncio.CancelledError):
                await submit_digital_human_task({"redis": redis_client}, task_id)
            async with SessionLocal() as db:
                interrupted = await db.get(VideoTask, task_id)
                assert interrupted.provider_task_id == "fake-video-1"
                assert interrupted.status == "pending"
            await submit_digital_human_task({"redis": redis_client}, task_id)
            await submit_digital_human_task({"redis": redis_client}, task_id)

        assert create_fake.await_count == 3
        assert all(
            call.kwargs["idempotency_key"] == task_id
            for call in create_fake.await_args_list
        )
        async with SessionLocal() as db:
            task = await db.get(VideoTask, task_id)
            job = await db.get(GenerationJob, job_id)
            user = await db.get(User, user_id)
            tx_count = await db.scalar(
                select(func.count()).select_from(CreditTransaction).where(
                    CreditTransaction.user_id == user_id
                )
            )
            assert (task.status, task.provider_task_id, task.result_url) == (
                "done",
                "fake-video-1",
                "https://example.test/result.mp4",
            )
            assert job.status == "done"
            assert user.credits == 100
            assert tx_count == 0
        status_key, _, _, progress_key = task_state_keys("video", task_id)
        assert await redis_client.get(status_key) == "done"
        assert await redis_client.get(progress_key) == "100"
    finally:
        await cleanup_case(redis_client, user_id, job_id, task_id)
        await redis_client.aclose()


async def test_translation_failure_refunds_once_after_duplicate_execution():
    redis_client = redis_async.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
    )
    user_id, job_id, task_id = await create_case(
        "video_translation", credits=90, credit_cost=10
    )
    create_fake = AsyncMock(
        return_value={"video_translation_id": "fake-translation-1", "status": "pending"}
    )
    try:
        with (
            patch("app.worker.heygen_tasks.create_video_translation", create_fake),
            patch(
                "app.worker.heygen_tasks.get_video_translation",
                AsyncMock(return_value={"status": "failed", "error_message": "fake failure"}),
            ),
        ):
            await submit_video_translation_task({"redis": redis_client}, task_id)
            await submit_video_translation_task({"redis": redis_client}, task_id)

        create_fake.assert_awaited_once()
        assert create_fake.await_args.kwargs["idempotency_key"] == task_id
        async with SessionLocal() as db:
            task = await db.get(VideoTask, task_id)
            job = await db.get(GenerationJob, job_id)
            user = await db.get(User, user_id)
            refunds = (
                await db.execute(
                    select(CreditTransaction).where(
                        CreditTransaction.user_id == user_id,
                        CreditTransaction.type == "refund",
                    )
                )
            ).scalars().all()
            assert task.status == "failed"
            assert task.provider_task_id == "fake-translation-1"
            assert task.credit_refunded is True
            assert job.status == "failed"
            assert user.credits == 100
            assert len(refunds) == 1
            assert refunds[0].credits_delta == 10
        status_key = task_state_keys("video", task_id)[0]
        assert await redis_client.get(status_key) == "failed"
    finally:
        await cleanup_case(redis_client, user_id, job_id, task_id)
        await redis_client.aclose()
