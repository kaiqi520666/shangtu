from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.distribution import apply_order_commissions, build_distribution_snapshot
from app.core.json_utils import dump_json, parse_json_or_none
from app.core.user_credits import calculate_user_credit_cost


def test_user_credit_cost_rounds_up_after_multiplier():
    assert calculate_user_credit_cost(7, "0.95") == 7
    assert calculate_user_credit_cost(21, "0.95") == 20
    assert calculate_user_credit_cost(7, "1.20") == 9


@pytest.mark.asyncio
async def test_distribution_snapshot_builds_grade_differences():
    users = {
        3: SimpleNamespace(
            id=3, distribution_level=3, distribution_parent_id=2,
            commission_rate=5, distribution_enabled=True,
        ),
        2: SimpleNamespace(
            id=2, distribution_level=2, distribution_parent_id=1,
            commission_rate=8, distribution_enabled=True,
        ),
        1: SimpleNamespace(
            id=1, distribution_level=1, distribution_parent_id=None,
            commission_rate=10, distribution_enabled=True,
        ),
    }
    db = AsyncMock()
    db.get.side_effect = lambda _model, user_id: users[user_id]

    snapshot_json, root_user_id = await build_distribution_snapshot(db, 3)

    assert root_user_id == 1
    assert parse_json_or_none(snapshot_json)["allocations"] == [
        {"user_id": 3, "rate": "5.00"},
        {"user_id": 2, "rate": "3.00"},
        {"user_id": 1, "rate": "2.00"},
    ]


@pytest.mark.asyncio
async def test_order_commission_updates_wallets_in_cents():
    users = [
        SimpleNamespace(id=1, commission_available_cents=0, commission_frozen_cents=0),
        SimpleNamespace(id=2, commission_available_cents=0, commission_frozen_cents=0),
        SimpleNamespace(id=3, commission_available_cents=0, commission_frozen_cents=0),
    ]
    result = Mock()
    result.scalars.return_value.all.return_value = users
    db = SimpleNamespace(execute=AsyncMock(return_value=result), add=Mock())
    order = SimpleNamespace(
        id="order-1",
        user_id=3,
        out_trade_no="trade-1",
        amount_cents=10000,
        distribution_snapshot_json=dump_json(
            {
                "source_user_id": 3,
                "allocations": [
                    {"user_id": 3, "rate": "5.00"},
                    {"user_id": 2, "rate": "3.00"},
                    {"user_id": 1, "rate": "2.00"},
                ],
            }
        ),
    )

    await apply_order_commissions(db, order)

    assert [user.commission_available_cents for user in users] == [200, 300, 500]
    assert db.add.call_count == 3
