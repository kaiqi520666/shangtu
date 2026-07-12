import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.schemas.response import fail
from app.services.video_translation import archive_task, create_task, get_task_details


def database():
    return SimpleNamespace(
        add=Mock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
        refresh=AsyncMock(),
        execute=AsyncMock(),
    )


def language():
    return SimpleNamespace(
        id="english",
        name="English",
        display_name_zh="英语",
        provider="heygen",
        sort_order=10,
    )


async def create_translation(db, redis, **overrides):
    values = {
        "user_id": 7,
        "get_redis_pool": lambda: redis,
        "video_url": " https://example.test/source.mp4 ",
        "duration_seconds": 5.2,
        "target_language_id": "english",
        "quality_tier": "standard",
        "source": "upload",
        "asset_task_id": None,
        "job_id": None,
        "requested_title": "商品翻译",
    }
    values.update(overrides)
    return await create_task(db, **values)


@pytest.mark.asyncio
async def test_create_task_persists_snapshot_and_enqueues():
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock())
    job = SimpleNamespace(id="job-1", status="draft", updated_at=None)
    with (
        patch("app.services.video_translation.get_enabled_language", AsyncMock(return_value=language())),
        patch(
            "app.services.video_translation.get_effective_video_translation_credit_costs",
            AsyncMock(return_value={"standard": 3, "premium": 5}),
        ),
        patch("app.services.video_translation.get_or_create_video_job", AsyncMock(return_value=job)),
        patch(
            "app.services.video_translation.deduct_credits_or_fail",
            AsyncMock(return_value=(SimpleNamespace(cost=18, balance_after=82), None)),
        ),
    ):
        response = await create_translation(db, redis)

    assert response.code == 0
    assert response.data["job_id"] == "job-1"
    assert response.data["credit_cost"] == 18
    task = db.add.call_args.args[0]
    assert (task.duration, task.input_video_url, task.status) == (
        6,
        "https://example.test/source.mp4",
        "pending",
    )
    snapshot = json.loads(task.settings_snapshot_json)
    assert snapshot["scene"]["durationSeconds"] == 6
    assert snapshot["scene"]["creditCost"] == 18
    assert (job.status, task.credit_cost) == ("generating", 18)
    redis.enqueue_job.assert_awaited_once_with("submit_video_translation_task", task.id)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_task_rejects_unavailable_language_before_charging():
    db = database()
    with (
        patch("app.services.video_translation.get_enabled_language", AsyncMock(return_value=None)),
        patch("app.services.video_translation.deduct_credits_or_fail", AsyncMock()) as deduct,
    ):
        response = await create_translation(db, SimpleNamespace())

    assert response.message == "目标语言不存在或已停用"
    deduct.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_task_returns_credit_validation_failure():
    db = database()
    job = SimpleNamespace(id="job-1", status="draft", updated_at=None)
    credit_failure = fail("积分不足")
    with (
        patch("app.services.video_translation.get_enabled_language", AsyncMock(return_value=language())),
        patch(
            "app.services.video_translation.get_effective_video_translation_credit_costs",
            AsyncMock(return_value={"standard": 3, "premium": 5}),
        ),
        patch("app.services.video_translation.get_or_create_video_job", AsyncMock(return_value=job)),
        patch(
            "app.services.video_translation.deduct_credits_or_fail",
            AsyncMock(return_value=(None, credit_failure)),
        ),
    ):
        response = await create_translation(db, SimpleNamespace())

    assert response is credit_failure
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_task_compensates_enqueue_failure():
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock(side_effect=RuntimeError("offline")))
    job = SimpleNamespace(id="job-1", status="draft", updated_at=None)
    with (
        patch("app.services.video_translation.get_enabled_language", AsyncMock(return_value=language())),
        patch(
            "app.services.video_translation.get_effective_video_translation_credit_costs",
            AsyncMock(return_value={"standard": 3, "premium": 5}),
        ),
        patch("app.services.video_translation.get_or_create_video_job", AsyncMock(return_value=job)),
        patch(
            "app.services.video_translation.deduct_credits_or_fail",
            AsyncMock(return_value=(SimpleNamespace(cost=18, balance_after=82), None)),
        ),
        patch("app.services.video_translation.refund_user_credits", AsyncMock(return_value=100)) as refund,
    ):
        response = await create_translation(db, redis)

    task = db.add.call_args.args[0]
    assert response.message == "视频翻译任务入队失败，请稍后重试"
    assert response.data == {
        "task_id": task.id,
        "job_id": "job-1",
        "credits": 100,
        "credit_cost": 18,
    }
    refund.assert_awaited_once()
    assert db.commit.await_count == 2
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_task_details_includes_latest_credits():
    db = database()
    task = SimpleNamespace(id="task-1")
    with (
        patch("app.services.video_translation.get_task", AsyncMock(return_value=task)),
        patch(
            "app.services.video_translation.task_payload",
            return_value={"task_id": "task-1", "credits": None},
        ),
        patch("app.services.video_translation.get_user_credits", AsyncMock(return_value=77)),
    ):
        payload = await get_task_details(db, task_id="task-1", user_id=7)

    assert payload == {"task_id": "task-1", "credits": 77}


@pytest.mark.asyncio
async def test_archive_task_syncs_workspace_status_before_commit():
    db = database()
    task = SimpleNamespace(
        id="task-1",
        job_id="job-1",
        archived=False,
        archived_at=None,
    )
    with (
        patch("app.services.video_translation.get_task", AsyncMock(return_value=task)),
        patch("app.services.video_translation.sync_video_job_status", AsyncMock()) as sync_job,
    ):
        error_message = await archive_task(db, task_id="task-1", user_id=7)

    assert error_message is None
    assert task.archived is True
    assert task.archived_at is not None
    sync_job.assert_awaited_once_with(db, job_id="job-1", scenario="video_translation")
    db.commit.assert_awaited_once()
