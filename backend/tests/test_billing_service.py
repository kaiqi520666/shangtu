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


def notification_params(**overrides):
    params = {
        "pid": "merchant-1",
        "trade_status": "TRADE_SUCCESS",
        "out_trade_no": "trade-1",
        "trade_no": "provider-1",
        "money": "9.90",
        "sign_type": "MD5",
    }
    params.update(overrides)
    params["sign"] = sign_params(params, "secret")
    return params


def pending_order(**overrides):
    values = {
        "id": "order-1",
        "user_id": 7,
        "out_trade_no": "trade-1",
        "amount_cents": 990,
        "credits": 100,
        "package_name": "入门包",
        "status": "pending",
        "provider_trade_no": None,
        "error_message": None,
        "paid_at": None,
        "updated_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def scalar_result(value):
    result = Mock()
    result.scalar_one_or_none.return_value = value
    return result


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
    order = pending_order()
    user = SimpleNamespace(id=7, credits=20)
    order_result = scalar_result(order)
    user_result = scalar_result(user)
    db = database()
    db.execute.side_effect = [order_result, user_result, order_result]
    db.begin.return_value = async_context()
    params = notification_params()

    with (
        patch("app.services.billing.get_zpay_pid", return_value="merchant-1"),
        patch("app.services.billing.get_zpay_key", return_value="secret"),
        patch("app.services.billing.apply_order_commissions", AsyncMock()) as commissions,
    ):
        first_result = await process_zpay_notification(db, params)
        second_result = await process_zpay_notification(db, params)

    assert (first_result, second_result) == ("success", "success")
    assert order.status == "paid"
    assert order.provider_trade_no == "provider-1"
    assert user.credits == 120
    transaction = db.add.call_args.args[0]
    assert transaction.credits_delta == 100
    assert transaction.balance_after == 120
    assert db.add.call_count == 1
    commissions.assert_awaited_once_with(db, order)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"sign": "invalid"}, "fail"),
        (notification_params(pid="other-merchant"), "fail"),
        (notification_params(trade_status="WAIT_BUYER_PAY"), "success"),
        (notification_params(money="invalid"), "fail"),
    ],
)
async def test_process_zpay_notification_rejects_invalid_callback(params, expected):
    db = database()
    with (
        patch("app.services.billing.get_zpay_pid", return_value="merchant-1"),
        patch("app.services.billing.get_zpay_key", return_value="secret"),
    ):
        result = await process_zpay_notification(db, params)

    assert result == expected
    db.execute.assert_not_awaited()
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_process_zpay_notification_rejects_unknown_order():
    db = database()
    db.execute.return_value = scalar_result(None)
    transaction = async_context()
    db.begin.return_value = transaction

    with (
        patch("app.services.billing.get_zpay_pid", return_value="merchant-1"),
        patch("app.services.billing.get_zpay_key", return_value="secret"),
    ):
        result = await process_zpay_notification(db, notification_params())

    assert result == "fail"
    db.add.assert_not_called()
    transaction.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_zpay_notification_rejects_amount_mismatch():
    order = pending_order()
    db = database()
    db.execute.return_value = scalar_result(order)
    db.begin.return_value = async_context()

    with (
        patch("app.services.billing.get_zpay_pid", return_value="merchant-1"),
        patch("app.services.billing.get_zpay_key", return_value="secret"),
    ):
        result = await process_zpay_notification(
            db,
            notification_params(money="10.00"),
        )

    assert result == "fail"
    assert order.status == "pending"
    assert order.error_message == "支付回调金额不一致"
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_process_zpay_notification_rejects_missing_user():
    order = pending_order()
    db = database()
    db.execute.side_effect = [scalar_result(order), scalar_result(None)]
    db.begin.return_value = async_context()

    with (
        patch("app.services.billing.get_zpay_pid", return_value="merchant-1"),
        patch("app.services.billing.get_zpay_key", return_value="secret"),
    ):
        result = await process_zpay_notification(db, notification_params())

    assert result == "fail"
    assert order.status == "pending"
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_process_zpay_notification_propagates_commission_failure_to_transaction():
    order = pending_order()
    user = SimpleNamespace(id=7, credits=20)
    db = database()
    db.execute.side_effect = [scalar_result(order), scalar_result(user)]
    transaction = async_context()
    db.begin.return_value = transaction

    with (
        patch("app.services.billing.get_zpay_pid", return_value="merchant-1"),
        patch("app.services.billing.get_zpay_key", return_value="secret"),
        patch(
            "app.services.billing.apply_order_commissions",
            AsyncMock(side_effect=RuntimeError("commission failed")),
        ),
        pytest.raises(RuntimeError, match="commission failed"),
    ):
        await process_zpay_notification(db, notification_params())

    exit_args = transaction.__aexit__.await_args.args
    assert exit_args[0] is RuntimeError
    assert db.add.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_point", ["http", "json"])
async def test_create_credit_order_marks_order_failed_on_provider_exception(failure_point):
    db = database()
    response = Mock()
    client = SimpleNamespace(post=AsyncMock(return_value=response))
    if failure_point == "http":
        client.post.side_effect = RuntimeError("network failed")
    else:
        response.json.side_effect = ValueError("invalid json")
    package = {
        "id": "starter",
        "name": "入门包",
        "credits": 100,
        "amount_cents": 990,
    }

    with (
        patch("app.services.billing.get_effective_recharge_packages", AsyncMock(return_value=[package])),
        patch("app.services.billing.build_distribution_snapshot", AsyncMock(return_value=(None, None))),
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

    assert outcome.error_message == "支付订单创建失败，请稍后重试"
    assert outcome.order.status == "failed"
    assert outcome.order.error_message == "支付订单创建失败"
    assert db.commit.await_count == 2
