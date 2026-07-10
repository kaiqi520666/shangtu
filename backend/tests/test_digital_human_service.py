from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import httpx

from app.services.digital_human import settle_task_credits_if_needed, sync_task_from_provider


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
        "settings_snapshot_json": None,
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
        patch("app.services.digital_human.deduct_user_credits_allow_negative", AsyncMock()) as deduct,
    ):
        assert await settle_task_credits_if_needed(db, task) is True
    deduct.assert_awaited_once_with(db, 7, 5, note="数字人结算补扣 · task-1")
    assert task.credit_cost == 15


@pytest.mark.asyncio
async def test_settlement_skips_refunded_task():
    assert await settle_task_credits_if_needed(AsyncMock(), make_task(credit_refunded=True)) is False


@pytest.mark.asyncio
async def test_provider_error_propagates_without_committing():
    db = AsyncMock()
    task = make_task(provider_task_id="provider-1")
    with patch("app.services.digital_human.get_video", AsyncMock(side_effect=httpx.ConnectError("offline"))):
        with pytest.raises(httpx.ConnectError):
            await sync_task_from_provider(db, task)
    db.commit.assert_not_awaited()
