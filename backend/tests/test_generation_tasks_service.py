import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.user_credits import CreditCharge
from app.services.generation_tasks import deduct_credits_or_fail, enqueue_or_compensate


def database():
    return SimpleNamespace(
        get=AsyncMock(return_value=SimpleNamespace(consumption_multiplier="1.5")),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )


def enqueue_args(db, redis, **overrides):
    values = {
        "get_redis_pool": lambda: redis,
        "db": db,
        "job_name": "generate_image",
        "job_args": ("task-1", "prompt"),
        "user_id": 7,
        "credit_cost": 12,
        "remaining_credits": 88,
        "refund_credits": AsyncMock(return_value=100),
        "mark_failed": AsyncMock(),
        "failure_message": "任务入队失败",
        "failure_data": {"task_id": "task-1", "job_id": "job-1"},
        "refund_note": "入队失败退回",
    }
    values.update(overrides)
    return values


@pytest.mark.asyncio
async def test_enqueue_or_compensate_returns_none_after_enqueue():
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock())
    args = enqueue_args(db, redis)

    response = await enqueue_or_compensate(**args)

    assert response is None
    redis.enqueue_job.assert_awaited_once_with("generate_image", "task-1", "prompt")
    args["refund_credits"].assert_not_awaited()
    args["mark_failed"].assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_enqueue_or_compensate_runs_before_enqueue():
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock())
    before_enqueue = AsyncMock()

    response = await enqueue_or_compensate(
        **enqueue_args(db, redis, before_enqueue=before_enqueue)
    )

    assert response is None
    before_enqueue.assert_awaited_once_with(redis)


@pytest.mark.asyncio
async def test_enqueue_or_compensate_refunds_and_marks_failed(caplog):
    db = database()
    redis = SimpleNamespace(
        enqueue_job=AsyncMock(side_effect=ConnectionError("redis unavailable"))
    )
    args = enqueue_args(db, redis)

    with caplog.at_level(logging.WARNING, logger="app.services.generation_tasks"):
        response = await enqueue_or_compensate(**args)

    assert response.message == "任务入队失败"
    assert response.data == {
        "task_id": "task-1",
        "job_id": "job-1",
        "credits": 100,
        "credit_cost": 12,
    }
    args["refund_credits"].assert_awaited_once_with(db, 7, 12, "入队失败退回")
    args["mark_failed"].assert_awaited_once_with(100)
    db.commit.assert_awaited_once()
    assert caplog.records[0].event == "generation_enqueue_failed"
    assert caplog.records[0].task_id == "task-1"


@pytest.mark.asyncio
@pytest.mark.parametrize("failed_step", ["refund", "mark", "commit"])
async def test_enqueue_or_compensate_rolls_back_failed_compensation(
    failed_step, caplog
):
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock(side_effect=TimeoutError("unknown")))
    args = enqueue_args(db, redis)
    if failed_step == "refund":
        args["refund_credits"].side_effect = RuntimeError("refund failed")
    elif failed_step == "mark":
        args["mark_failed"].side_effect = RuntimeError("mark failed")
    else:
        db.commit.side_effect = RuntimeError("commit failed")

    with caplog.at_level(logging.WARNING, logger="app.services.generation_tasks"):
        response = await enqueue_or_compensate(**args)

    assert response.data["credits"] == 88
    db.rollback.assert_awaited_once()
    assert [record.event for record in caplog.records] == [
        "generation_enqueue_failed",
        "generation_compensation_failed",
    ]


@pytest.mark.asyncio
async def test_deduct_credits_or_fail_returns_charge():
    db = database()
    charge = CreditCharge(cost=15, balance_after=85, multiplier="1.5")
    with patch(
        "app.services.generation_tasks.charge_user_credits",
        AsyncMock(return_value=charge),
    ) as charge_credits:
        result, response = await deduct_credits_or_fail(db, 7, 10, note="生图")

    assert (result, response) == (charge, None)
    charge_credits.assert_awaited_once_with(db, 7, 10, note="生图")
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_deduct_credits_or_fail_returns_latest_balance():
    db = database()
    with (
        patch(
            "app.services.generation_tasks.charge_user_credits",
            AsyncMock(return_value=None),
        ),
        patch(
            "app.services.generation_tasks.get_user_credits",
            AsyncMock(return_value=4),
        ) as get_credits,
    ):
        result, response = await deduct_credits_or_fail(db, 7, 10)

    assert result is None
    assert response.message == "积分不足，本次需要 15 点，当前剩余 4 点"
    db.rollback.assert_awaited_once()
    get_credits.assert_awaited_once_with(db, 7)
