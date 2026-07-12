from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from app.core.json_utils import dump_json

from app.services.digital_human import (
    archive_task,
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
