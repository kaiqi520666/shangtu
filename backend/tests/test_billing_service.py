from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.core.providers.zpay import sign_params
from app.services.billing import create_credit_order, process_zpay_notification


def database():
    async def refresh(instance):
        if instance.id is None:
            instance.id = "order-1"

    return SimpleNamespace(
        add=Mock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
        refresh=AsyncMock(side_effect=refresh),
        execute=AsyncMock(),
        begin=MagicMock(),
    )


def async_context(value=None):
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=value)
    context.__aexit__ = AsyncMock(return_value=None)
    return context


@pytest.mark.asyncio
async def test_create_credit_order_persists_and_creates_zpay_payment():
    db = database()
    response = Mock()
    response.json.return_value = {
        "code": 1,
        "trade_no": "provider-1",
        "payurl": "https://pay.example.test/order-1",
        "qrcode": "wx://order-1",
    }
    client = SimpleNamespace(post=AsyncMock(return_value=response))
    package = {
        "id": "starter",
        "name": "入门包",
        "credits": 100,
        "amount_cents": 990,
    }

    with (
        patch(
            "app.services.billing.get_effective_recharge_packages",
            AsyncMock(return_value=[package]),
        ),
        patch(
            "app.services.billing.build_distribution_snapshot",
            AsyncMock(return_value=(None, None)),
        ),
        patch("app.services.billing.get_zpay_pid", return_value="merchant-1"),
        patch("app.services.billing.get_zpay_key", return_value="secret"),
        patch("app.services.billing.get_zpay_gateway", return_value="https://pay.example.test"),
        patch(
            "app.services.billing.get_zpay_notify_url",
            return_value="https://api.example.test/notify",
        ),
        patch(
            "app.services.billing.get_zpay_return_url",
            return_value="https://app.example.test/return",
        ),
        patch("app.services.billing._make_out_trade_no", return_value="trade-1"),
        patch("app.services.billing.httpx.AsyncClient", return_value=async_context(client)),
    ):
        outcome = await create_credit_order(
            db=db,
            current_user=SimpleNamespace(id=7),
            package_id="starter",
            client_ip="203.0.113.8",
        )

    assert outcome.error_message is None
    assert outcome.order.provider_trade_no == "provider-1"
    assert outcome.order.pay_url == "https://pay.example.test/order-1"
    assert db.commit.await_count == 2
    client.post.assert_awaited_once()
    endpoint = client.post.await_args.args[0]
    payload = client.post.await_args.kwargs["data"]
    assert endpoint == "https://pay.example.test/mapi.php"
    assert payload["clientip"] == "203.0.113.8"
    assert payload["param"] == "order-1"
    assert payload["sign"] == sign_params(payload, "secret")


@pytest.mark.asyncio
async def test_create_credit_order_returns_provider_failure_with_order():
    db = database()
    response = Mock()
    response.json.return_value = {"code": 0, "msg": "通道不可用"}
    client = SimpleNamespace(post=AsyncMock(return_value=response))
    package = {
        "id": "starter",
        "name": "入门包",
        "credits": 100,
        "amount_cents": 990,
    }

    with (
        patch(
            "app.services.billing.get_effective_recharge_packages",
            AsyncMock(return_value=[package]),
        ),
        patch(
            "app.services.billing.build_distribution_snapshot",
            AsyncMock(return_value=(None, None)),
        ),
        patch("app.services.billing.get_zpay_pid", return_value="merchant-1"),
        patch("app.services.billing.get_zpay_key", return_value="secret"),
        patch("app.services.billing.get_zpay_gateway", return_value="https://pay.example.test"),
        patch("app.services.billing.get_zpay_notify_url", return_value="notify"),
        patch("app.services.billing.get_zpay_return_url", return_value="return"),
        patch("app.services.billing.httpx.AsyncClient", return_value=async_context(client)),
    ):
        outcome = await create_credit_order(
            db=db,
            current_user=SimpleNamespace(id=7),
            package_id="starter",
            client_ip="203.0.113.8",
        )

    assert outcome.error_message == "通道不可用"
    assert outcome.order.status == "failed"
    assert outcome.order.error_message == "通道不可用"


@pytest.mark.asyncio
async def test_process_zpay_notification_credits_user_once():
    order = SimpleNamespace(
        id="order-1",
        user_id=7,
        out_trade_no="trade-1",
        amount_cents=990,
        credits=100,
        package_name="入门包",
        status="pending",
        provider_trade_no=None,
        error_message=None,
        paid_at=None,
        updated_at=None,
    )
    user = SimpleNamespace(id=7, credits=20)
    order_result = Mock()
    order_result.scalar_one_or_none.return_value = order
    user_result = Mock()
    user_result.scalar_one_or_none.return_value = user
    db = database()
    db.execute.side_effect = [order_result, user_result]
    db.begin.return_value = async_context()
    params = {
        "pid": "merchant-1",
        "trade_status": "TRADE_SUCCESS",
        "out_trade_no": "trade-1",
        "trade_no": "provider-1",
        "money": "9.90",
        "sign_type": "MD5",
    }
    params["sign"] = sign_params(params, "secret")

    with (
        patch("app.services.billing.get_zpay_pid", return_value="merchant-1"),
        patch("app.services.billing.get_zpay_key", return_value="secret"),
        patch("app.services.billing.apply_order_commissions", AsyncMock()) as commissions,
    ):
        result = await process_zpay_notification(db, params)

    assert result == "success"
    assert order.status == "paid"
    assert order.provider_trade_no == "provider-1"
    assert user.credits == 120
    transaction = db.add.call_args.args[0]
    assert transaction.credits_delta == 100
    assert transaction.balance_after == 120
    commissions.assert_awaited_once_with(db, order)