from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.core.coupons import normalize_coupon_code, redeem_coupon
from app.core.time import utc_now
from app.models import CouponRedemption, CreditTransaction
from app.routers.admin.coupon_codes import delete_coupon_code, update_coupon_code
from app.routers.admin.schemas import CreateCouponCodeRequest, UpdateCouponCodeRequest


def coupon(**overrides):
    values = {
        "id": "coupon-1",
        "code": "WELCOME-2026",
        "credits": 100,
        "usage_limit": 10,
        "used_count": 2,
        "enabled": True,
        "deleted_at": None,
        "created_by_user_id": 99,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def user(**overrides):
    values = {"id": 1, "email": "user@example.com", "credits": 50, "role": "user"}
    values.update(overrides)
    return SimpleNamespace(**values)


def result(value, *, optional=False):
    row = Mock()
    if optional:
        row.scalar_one_or_none.return_value = value
    else:
        row.scalar_one.return_value = value
    return row


def test_coupon_code_normalization_and_validation():
    assert normalize_coupon_code(" welcome-2026 ") == "WELCOME-2026"
    assert CreateCouponCodeRequest(
        code=" lower-123 ", credits=10, usage_limit=None
    ).code == "LOWER-123"
    with pytest.raises(ValueError):
        normalize_coupon_code("bad code")
    with pytest.raises(ValidationError):
        CreateCouponCodeRequest(code="ABC", credits=10)


@pytest.mark.asyncio
async def test_redeem_coupon_updates_all_balances_and_snapshots():
    item = coupon(credits=120, used_count=0)
    target = user()
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[result(item, optional=True), result(target)]),
        scalar=AsyncMock(return_value=None),
        add=Mock(),
        flush=AsyncMock(),
    )

    redeemed_coupon, redeemed_user = await redeem_coupon(db, target.id, item.code)

    assert redeemed_coupon is item
    assert redeemed_user.credits == 170
    assert item.used_count == 1
    transaction = next(call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], CreditTransaction))
    redemption = next(call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], CouponRedemption))
    assert transaction.type == "coupon_redeem"
    assert transaction.balance_after == 170
    assert redemption.code_snapshot == "WELCOME-2026"
    assert redemption.credits_snapshot == 120
    statements = [call.args[0] for call in db.execute.await_args_list]
    compiled = [str(stmt.compile(dialect=postgresql.dialect())) for stmt in statements]
    assert all("FOR UPDATE" in sql for sql in compiled)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"enabled": False}, "已停用"),
        ({"deleted_at": utc_now()}, "不存在或已删除"),
        ({"used_count": 10}, "使用次数已用完"),
    ],
)
async def test_redeem_coupon_rejects_unavailable_codes(overrides, message):
    db = SimpleNamespace(execute=AsyncMock(return_value=result(coupon(**overrides), optional=True)))
    with pytest.raises(ValueError, match=message):
        await redeem_coupon(db, 1, "WELCOME-2026")


@pytest.mark.asyncio
async def test_redeem_coupon_rejects_same_user_twice():
    db = SimpleNamespace(
        execute=AsyncMock(return_value=result(coupon(), optional=True)),
        scalar=AsyncMock(return_value="redemption-1"),
    )
    with pytest.raises(ValueError, match="已经兑换"):
        await redeem_coupon(db, 1, "WELCOME-2026")


@pytest.mark.asyncio
async def test_update_coupon_limit_cannot_drop_below_usage():
    item = coupon(used_count=5)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=result(item, optional=True)),
        add=Mock(),
        commit=AsyncMock(),
    )
    response = await update_coupon_code(
        item.id,
        UpdateCouponCodeRequest(usage_limit=4),
        user(id=99, role="super_admin"),
        db,
    )
    assert response.code != 0
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_coupon_can_switch_to_unlimited():
    item = coupon(used_count=5)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=result(item, optional=True)),
        add=Mock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )
    response = await update_coupon_code(
        item.id,
        UpdateCouponCodeRequest(usage_limit=None),
        user(id=99, role="super_admin"),
        db,
    )
    assert response.code == 0
    assert item.usage_limit is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_coupon_is_soft_delete_with_audit():
    item = coupon()
    db = SimpleNamespace(
        execute=AsyncMock(return_value=result(item, optional=True)),
        add=Mock(),
        commit=AsyncMock(),
    )
    response = await delete_coupon_code(
        item.id,
        user(id=99, role="super_admin"),
        db,
    )
    assert response.code == 0
    assert item.enabled is False
    assert item.deleted_at is not None
    audit = db.add.call_args.args[0]
    assert audit.action == "delete_coupon_code"
