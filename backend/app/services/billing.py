import uuid
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.distribution import apply_order_commissions, build_distribution_snapshot
from app.core.json_utils import dump_json
from app.core.providers.zpay import (
    format_amount,
    get_zpay_gateway,
    get_zpay_key,
    get_zpay_notify_url,
    get_zpay_pid,
    get_zpay_return_url,
    parse_amount_cents,
    sign_params,
)
from app.core.system_settings import get_effective_recharge_packages
from app.core.time import utc_now
from app.models import CreditOrder, CreditTransaction, User


@dataclass(slots=True)
class CreditOrderCreation:
    order: CreditOrder | None
    error_message: str | None = None


def _make_out_trade_no() -> str:
    suffix = uuid.uuid4().int % 10**8
    return f"{utc_now():%y%m%d%H%M%S}{suffix:08d}"


async def create_credit_order(
    *,
    db: AsyncSession,
    current_user: User,
    package_id: str,
    client_ip: str,
) -> CreditOrderCreation:
    try:
        packages = await get_effective_recharge_packages(db)
        package = next((item for item in packages if item["id"] == package_id), None)
        if not package:
            return CreditOrderCreation(None, "充值套餐不存在或已下架")
        pid = get_zpay_pid()
        key = get_zpay_key()
        gateway = get_zpay_gateway()
        notify_url = get_zpay_notify_url()
        return_url = get_zpay_return_url()
    except ValueError as exc:
        return CreditOrderCreation(None, str(exc))

    out_trade_no = _make_out_trade_no()
    distribution_snapshot_json, distribution_root_user_id = await build_distribution_snapshot(
        db, current_user.id
    )
    order = CreditOrder(
        user_id=current_user.id,
        out_trade_no=out_trade_no,
        package_id=package["id"],
        package_name=package["name"],
        package_snapshot_json=dump_json(package),
        distribution_snapshot_json=distribution_snapshot_json,
        distribution_root_user_id=distribution_root_user_id,
        credits=package["credits"],
        amount_cents=package["amount_cents"],
        pay_type="wxpay",
        status="pending",
    )
    db.add(order)
    try:
        await db.commit()
        await db.refresh(order)
    except Exception:
        await db.rollback()
        return CreditOrderCreation(None, "创建充值订单失败，请稍后重试")

    payload: dict[str, Any] = {
        "pid": pid,
        "type": "wxpay",
        "out_trade_no": out_trade_no,
        "notify_url": notify_url,
        "return_url": return_url,
        "name": f"商图AI积分充值-{package['name']}",
        "money": format_amount(package["amount_cents"]),
        "clientip": client_ip,
        "device": "pc",
        "param": order.id,
        "sign_type": "MD5",
    }
    payload["sign"] = sign_params(payload, key)

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{gateway}/mapi.php", data=payload)
            data = response.json()
    except Exception:
        order.status = "failed"
        order.error_message = "支付订单创建失败"
        order.updated_at = utc_now()
        await db.commit()
        return CreditOrderCreation(order, "支付订单创建失败，请稍后重试")

    if str(data.get("code")) != "1":
        order.status = "failed"
        order.error_message = str(data.get("msg") or "支付订单创建失败")
        order.updated_at = utc_now()
        await db.commit()
        return CreditOrderCreation(order, order.error_message)

    order.provider_trade_no = str(data.get("trade_no") or data.get("O_id") or "") or None
    order.pay_url = data.get("payurl") or None
    order.qr_code = data.get("qrcode") or None
    order.qr_img = data.get("img") or None
    order.updated_at = utc_now()
    await db.commit()
    await db.refresh(order)
    return CreditOrderCreation(order)


async def process_zpay_notification(
    db: AsyncSession,
    params: dict[str, str],
) -> Literal["success", "fail"]:
    try:
        key = get_zpay_key()
        pid = get_zpay_pid()
    except ValueError:
        return "fail"

    sign = params.get("sign")
    if not sign or sign.lower() != sign_params(params, key):
        return "fail"
    if str(params.get("pid") or "") != str(pid):
        return "fail"
    if params.get("trade_status") != "TRADE_SUCCESS":
        return "success"

    out_trade_no = params.get("out_trade_no")
    if not out_trade_no:
        return "fail"
    notify_amount_cents = parse_amount_cents(params.get("money"))
    if notify_amount_cents is None:
        return "fail"

    async with db.begin():
        result = await db.execute(
            select(CreditOrder)
            .where(CreditOrder.out_trade_no == out_trade_no)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            return "fail"
        if notify_amount_cents != order.amount_cents:
            order.error_message = "支付回调金额不一致"
            order.updated_at = utc_now()
            return "fail"
        if order.status == "paid":
            return "success"

        user_result = await db.execute(
            select(User).where(User.id == order.user_id).with_for_update()
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return "fail"

        trade_no = params.get("trade_no")
        order.status = "paid"
        order.provider_trade_no = trade_no or order.provider_trade_no
        order.paid_at = utc_now()
        order.updated_at = order.paid_at
        user.credits += order.credits
        db.add(
            CreditTransaction(
                user_id=user.id,
                order_id=order.id,
                type="recharge",
                credits_delta=order.credits,
                balance_after=user.credits,
                note=f"{order.package_name} 充值到账",
            )
        )
        await apply_order_commissions(db, order)

    return "success"