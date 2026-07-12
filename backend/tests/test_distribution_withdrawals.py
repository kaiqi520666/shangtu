from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.distribution import update_root_distribution
from app.core.time import utc_now
from app.models import CommissionWithdrawal
from app.routers.admin.commission_withdrawals import (
    RejectWithdrawalRequest,
    reject_withdrawal,
)
from app.routers.distribution import CreateWithdrawalRequest, create_withdrawal


def user(**overrides):
    values = {
        "id": 1,
        "distribution_level": 1,
        "distribution_parent_id": None,
        "distribution_enabled": True,
        "commission_rate": Decimal("10.00"),
        "commission_available_cents": 30000,
        "commission_frozen_cents": 0,
        "commission_withdrawn_cents": 0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_withdrawal_requires_hundred_yuan_multiple():
    response = await create_withdrawal(
        CreateWithdrawalRequest(
            amount_cents=15000,
            alipay_name="张三",
            alipay_account="user@example.com",
        ),
        user(),
        AsyncMock(),
    )
    assert response.code != 0


@pytest.mark.asyncio
async def test_withdrawal_freezes_available_commission():
    target = user()
    result = Mock()
    result.scalar_one.return_value = target
    db = SimpleNamespace(
        execute=AsyncMock(return_value=result),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )
    response = await create_withdrawal(
        CreateWithdrawalRequest(
            amount_cents=10000,
            alipay_name="张三",
            alipay_account="user@example.com",
        ),
        target,
        db,
    )
    assert response.code == 0
    assert target.commission_available_cents == 20000
    assert target.commission_frozen_cents == 10000
    assert db.add.call_count == 2


@pytest.mark.asyncio
async def test_reject_withdrawal_returns_frozen_commission():
    now = utc_now()
    item = CommissionWithdrawal(
        id="withdrawal-1",
        user_id=1,
        amount_cents=10000,
        alipay_name="张三",
        alipay_account="user@example.com",
        status="pending_payment",
        created_at=now,
        updated_at=now,
    )
    target = user(commission_available_cents=20000, commission_frozen_cents=10000)
    item_result, user_result = Mock(), Mock()
    item_result.scalar_one_or_none.return_value = item
    user_result.scalar_one.return_value = target
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[item_result, user_result]),
        add=Mock(),
        commit=AsyncMock(),
    )
    admin = SimpleNamespace(id=99, email="admin@example.com")

    response = await reject_withdrawal(
        item.id,
        RejectWithdrawalRequest(reason="信息不一致"),
        admin,
        db,
    )
    assert response.code == 0
    assert item.status == "rejected"
    assert target.commission_available_cents == 30000
    assert target.commission_frozen_cents == 0


@pytest.mark.asyncio
async def test_stopping_distribution_invalidates_pending_snapshots():
    root = user()
    child_result, grandchild_result = Mock(), Mock()
    child_result.scalars.return_value = [2]
    grandchild_result.scalars.return_value = [3]
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[child_result, grandchild_result, Mock(), Mock()]
        ),
        scalar=AsyncMock(),
    )

    changed = await update_root_distribution(
        db, root, enabled=False, rate=None
    )

    assert changed is True
    assert root.distribution_enabled is False
    assert db.execute.await_count == 4
