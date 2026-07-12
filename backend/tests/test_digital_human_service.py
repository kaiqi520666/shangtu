import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.core.json_utils import dump_json

from app.services.digital_human import (
    archive_task,
    create_task,
    get_task_details,
    settle_task_credits_if_needed,
)


def make_task(**overrides):
    values = {
        "id": "task-1",
        "user_id": 7,
        "scenario": "digital_human",
        "status": "done",
        "credit_refunded": False,
        "credit_cost": 20,
        "duration": 5,
        "type_id": "standard",
        "settings_snapshot_json": dump_json({"billing": {"consumption_multiplier": "1.00"}}),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def database(*, commit_error: Exception | None = None):
    return SimpleNamespace(
        add=Mock(),
        commit=AsyncMock(side_effect=commit_error),
        rollback=AsyncMock(),
        refresh=AsyncMock(),
        execute=AsyncMock(),
    )


def avatar():
    return SimpleNamespace(
        avatar_id="avatar-1",
        name="演示数字人",
        preview_image_url="https://example.test/avatar.png",
        preview_video_url="https://example.test/avatar.mp4",
        source="system",
        asset_id="catalog-avatar-1",
        avatar_type="studio_avatar",
    )


def voice():
    return SimpleNamespace(
        voice_id="voice-1",
        name="普通话女声",
        language="zh-CN",
        preview_audio_url="https://example.test/voice.mp3",
    )


def audio_asset():
    return SimpleNamespace(
        id="audio-1",
        name="上传口播",
        audio_url="https://example.test/upload.mp3",
        duration_seconds=8,
    )


async def create_digital_human(db, redis, **overrides):
    values = {
        "user_id": 7,
        "get_redis_pool": lambda: redis,
        "job_id": None,
        "requested_title": "数字人演示",
        "avatar_id": "avatar-1",
        "voice_id": "voice-1",
        "audio_asset_id": None,
        "script": "欢迎了解这款商品",
        "background_url": None,
        "quality_tier": "standard",
        "resolution": "1080p",
        "aspect_ratio": "9:16",
        "voice_speed": 1.0,
    }
    values.update(overrides)
    return await create_task(db, **values)


def creation_patches(job):
    return (
        patch("app.services.digital_human.resolve_avatar", AsyncMock(return_value=avatar())),
        patch("app.services.digital_human.get_enabled_voice", AsyncMock(return_value=voice())),
        patch("app.services.digital_human.get_effective_digital_human_precharge_cost", AsyncMock(return_value=20)),
        patch("app.services.digital_human.get_or_create_job", AsyncMock(return_value=job)),
        patch(
            "app.services.digital_human.deduct_credits_or_fail",
            AsyncMock(return_value=(SimpleNamespace(cost=20, balance_after=80, multiplier=1), None)),
        ),
    )


@pytest.mark.asyncio
async def test_create_task_with_platform_voice_persists_and_enqueues():
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock())
    job = SimpleNamespace(id="job-1", status="draft", updated_at=None)
    patches = creation_patches(job)
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        response = await create_digital_human(db, redis)

    assert response.code == 0
    assert response.data == {
        "task_id": db.add.call_args.args[0].id,
        "job_id": "job-1",
        "provider_task_id": None,
        "status": "pending",
        "credits": 80,
        "credit_cost": 20,
    }
    task = db.add.call_args.args[0]
    snapshot = json.loads(task.settings_snapshot_json)
    assert task.prompt == "欢迎了解这款商品"
    assert snapshot["scene"]["audioMode"] == "platform"
    assert snapshot["scene"]["voiceId"] == "voice-1"
    assert snapshot["billing"] == {"consumption_multiplier": "1.00"}
    assert job.status == "generating"
    assert job.updated_at is not None
    redis.enqueue_job.assert_awaited_once_with("submit_digital_human_task", task.id)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_task_with_uploaded_audio_uses_owned_asset():
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock())
    job = SimpleNamespace(id="job-1", status="draft", updated_at=None)
    owned_audio = audio_asset()
    with (
        patch("app.services.digital_human.resolve_avatar", AsyncMock(return_value=avatar())),
        patch("app.services.digital_human.get_available_audio_asset", AsyncMock(return_value=owned_audio)) as get_audio,
        patch("app.services.digital_human.get_enabled_voice", AsyncMock()) as get_voice,
        patch("app.services.digital_human.get_effective_digital_human_precharge_cost", AsyncMock(return_value=20)),
        patch("app.services.digital_human.get_or_create_job", AsyncMock(return_value=job)),
        patch(
            "app.services.digital_human.deduct_credits_or_fail",
            AsyncMock(return_value=(SimpleNamespace(cost=20, balance_after=80, multiplier=1), None)),
        ),
    ):
        response = await create_digital_human(
            db,
            redis,
            voice_id=None,
            audio_asset_id="audio-1",
            script=None,
        )

    assert response.code == 0
    get_audio.assert_awaited_once_with(db, audio_asset_id="audio-1", user_id=7)
    get_voice.assert_not_awaited()
    task = db.add.call_args.args[0]
    snapshot = json.loads(task.settings_snapshot_json)
    assert task.prompt == "自定义音频：上传口播"
    assert snapshot["scene"]["audioMode"] == "upload"
    assert snapshot["scene"]["audioAssetId"] == "audio-1"
    assert snapshot["scene"]["audioDurationSeconds"] == 8


@pytest.mark.asyncio
async def test_create_task_rejects_unowned_avatar_before_loading_audio():
    db = database()
    with (
        patch("app.services.digital_human.resolve_avatar", AsyncMock(return_value=None)) as resolve,
        patch("app.services.digital_human.get_enabled_voice", AsyncMock()) as get_voice,
        patch("app.services.digital_human.deduct_credits_or_fail", AsyncMock()) as deduct,
    ):
        response = await create_digital_human(db, SimpleNamespace())

    assert response.message == "数字人不存在或已停用"
    resolve.assert_awaited_once_with(db, avatar_id="avatar-1", user_id=7)
    get_voice.assert_not_awaited()
    deduct.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_task_rejects_unowned_audio_before_charging():
    db = database()
    with (
        patch("app.services.digital_human.resolve_avatar", AsyncMock(return_value=avatar())),
        patch("app.services.digital_human.get_available_audio_asset", AsyncMock(return_value=None)) as get_audio,
        patch("app.services.digital_human.deduct_credits_or_fail", AsyncMock()) as deduct,
    ):
        response = await create_digital_human(
            db,
            SimpleNamespace(),
            voice_id=None,
            audio_asset_id="other-user-audio",
            script=None,
        )

    assert response.message == "上传音频不存在或已删除"
    get_audio.assert_awaited_once_with(db, audio_asset_id="other-user-audio", user_id=7)
    deduct.assert_not_awaited()
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_task_returns_credit_failure_without_persisting():
    db = database()
    job = SimpleNamespace(id="job-1", status="draft", updated_at=None)
    failure = SimpleNamespace(code=1, message="积分不足")
    with (
        patch("app.services.digital_human.resolve_avatar", AsyncMock(return_value=avatar())),
        patch("app.services.digital_human.get_enabled_voice", AsyncMock(return_value=voice())),
        patch("app.services.digital_human.get_effective_digital_human_precharge_cost", AsyncMock(return_value=20)),
        patch("app.services.digital_human.get_or_create_job", AsyncMock(return_value=job)),
        patch("app.services.digital_human.deduct_credits_or_fail", AsyncMock(return_value=(None, failure))),
    ):
        response = await create_digital_human(db, SimpleNamespace())

    assert response is failure
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    assert job.status == "draft"


@pytest.mark.asyncio
async def test_create_task_rolls_back_persistence_failure():
    db = database(commit_error=RuntimeError("database offline"))
    job = SimpleNamespace(id="job-1", status="draft", updated_at=None)
    patches = creation_patches(job)
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        response = await create_digital_human(db, SimpleNamespace())

    assert response.message == "数字人任务创建失败，请稍后重试"
    db.rollback.assert_awaited_once()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_task_compensates_enqueue_failure():
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock(side_effect=RuntimeError("redis offline")))
    job = SimpleNamespace(id="job-1", status="draft", updated_at=None)
    patches = creation_patches(job)
    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4],
        patch("app.services.digital_human.refund_user_credits", AsyncMock(return_value=100)) as refund,
    ):
        response = await create_digital_human(db, redis)

    task = db.add.call_args.args[0]
    assert response.message == "数字人任务入队失败，请稍后重试"
    assert response.data == {
        "task_id": task.id,
        "job_id": "job-1",
        "credits": 100,
        "credit_cost": 20,
    }
    refund.assert_awaited_once()
    db.execute.assert_awaited_once()
    assert db.commit.await_count == 2


@pytest.mark.asyncio
async def test_settlement_refunds_overcharge():
    db = AsyncMock()
    task = make_task()
    with (
        patch("app.services.digital_human.get_effective_digital_human_credit_costs", AsyncMock(return_value={"standard": 3})),
        patch("app.services.digital_human.refund_user_credits", AsyncMock()) as refund,
    ):
        assert await settle_task_credits_if_needed(db, task) is True
    refund.assert_awaited_once_with(db, 7, 5, note="数字人结算退回 · task-1")
    assert task.credit_cost == 15


@pytest.mark.asyncio
async def test_settlement_charges_underpayment():
    db = AsyncMock()
    task = make_task(credit_cost=10)
    with (
        patch("app.services.digital_human.get_effective_digital_human_credit_costs", AsyncMock(return_value={"standard": 3})),
        patch("app.services.digital_human.charge_user_credits", AsyncMock()) as deduct,
    ):
        assert await settle_task_credits_if_needed(db, task) is True
    deduct.assert_awaited_once_with(
        db,
        7,
        5,
        note="数字人结算补扣 · task-1",
        multiplier="1.00",
        allow_negative=True,
    )
    assert task.credit_cost == 15


@pytest.mark.asyncio
async def test_settlement_skips_refunded_task():
    assert await settle_task_credits_if_needed(AsyncMock(), make_task(credit_refunded=True)) is False


@pytest.mark.asyncio
async def test_get_task_details_includes_latest_credits():
    db = AsyncMock()
    task = make_task()
    payload = {"task_id": task.id, "status": "done"}
    with (
        patch("app.services.digital_human.get_task", AsyncMock(return_value=task)),
        patch("app.services.digital_human.task_payload", return_value=payload.copy()),
        patch("app.services.digital_human.get_user_credits", AsyncMock(return_value=80)),
    ):
        details = await get_task_details(db, task_id=task.id, user_id=task.user_id)

    assert details == {"task_id": task.id, "status": "done", "credits": 80}


@pytest.mark.asyncio
async def test_archive_task_syncs_job_before_commit():
    db = AsyncMock()
    task = make_task(job_id="job-1", archived=False, archived_at=None)
    with (
        patch("app.services.digital_human.get_task", AsyncMock(return_value=task)),
        patch("app.services.digital_human.sync_job_status", AsyncMock()) as sync_job,
    ):
        error_message = await archive_task(db, task_id=task.id, user_id=task.user_id)

    assert error_message is None
    assert task.archived is True
    assert task.archived_at is not None
    sync_job.assert_awaited_once_with(db, "job-1")
    db.commit.assert_awaited_once()
