import hashlib
import os
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.json_utils import dump_json
from app.core.system_settings import (
    get_effective_digital_human_credit_costs,
    get_effective_digital_human_precharge_costs,
    get_effective_image_credit_costs,
    get_effective_recharge_packages,
    get_effective_video_credit_costs,
)
from app.core.time import to_utc_iso, utc_now
from app.models import CreditOrder, CreditTransaction, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/billing", tags=["积分充值"])

class CreateOrderRequest(BaseModel):
    package_id: str


def _format_amount(amount_cents: int) -> str:
    amount = (Decimal(amount_cents) / Decimal(100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return f"{amount:.2f}"


def _parse_amount_cents(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(
            (Decimal(str(value)) * Decimal(100)).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
    except Exception:
        return None


def _zpay_key() -> str:
    key = os.getenv("ZPAY_KEY")
    if not key:
        raise ValueError("ZPAY_KEY 未配置")
    return key


def _zpay_pid() -> str:
    pid = os.getenv("ZPAY_PID")
    if not pid:
        raise ValueError("ZPAY_PID 未配置")
    return pid


def _zpay_gateway() -> str:
    return (os.getenv("ZPAY_GATEWAY") or "https://zpayz.cn").rstrip("/")


def _zpay_notify_url() -> str:
    url = os.getenv("ZPAY_NOTIFY_URL")
    if not url:
        raise ValueError("ZPAY_NOTIFY_URL 未配置")
    return url


def _zpay_return_url() -> str:
    url = os.getenv("ZPAY_RETURN_URL")
    if not url:
        raise ValueError("ZPAY_RETURN_URL 未配置")
    return url


def zpay_sign(params: dict[str, Any], key: str) -> str:
    items = []
    for name, value in params.items():
        if name in {"sign", "sign_type"}:
            continue
        if value is None or str(value) == "":
            continue
        items.append((name, str(value)))
    items.sort(key=lambda item: item[0])
    raw = "&".join(f"{name}={value}" for name, value in items)
    return hashlib.md5(f"{raw}{key}".encode("utf-8")).hexdigest()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


def _order_payload(order: CreditOrder, credits: int | None = None) -> dict[str, Any]:
    return {
        "order_id": order.id,
        "out_trade_no": order.out_trade_no,
        "provider_trade_no": order.provider_trade_no,
        "package_id": order.package_id,
        "package_name": order.package_name,
        "credits_to_add": order.credits,
        "amount_cents": order.amount_cents,
        "pay_type": order.pay_type,
        "status": order.status,
        "pay_url": order.pay_url,
        "qrcode": order.qr_code,
        "img": order.qr_img,
        "error_message": order.error_message,
        "created_at": to_utc_iso(order.created_at),
        "paid_at": to_utc_iso(order.paid_at),
        **({"credits": credits} if credits is not None else {}),
    }


def _make_out_trade_no() -> str:
    suffix = uuid.uuid4().int % 10**8
    return f"{utc_now():%y%m%d%H%M%S}{suffix:08d}"


@router.get("/packages", response_model=Response)
async def list_packages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        packages = await get_effective_recharge_packages(db)
        image_credit_costs = await get_effective_image_credit_costs(db)
        video_credit_costs = await get_effective_video_credit_costs(db)
        digital_human_credit_costs = await get_effective_digital_human_credit_costs(db)
        digital_human_precharge_costs = await get_effective_digital_human_precharge_costs(db)
    except ValueError as exc:
        return fail(str(exc))
    return success(
        {
            "packages": packages,
            "image_credit_costs": image_credit_costs,
            "video_credit_costs": video_credit_costs,
            "digital_human_credit_costs": digital_human_credit_costs,
            "digital_human_precharge_costs": digital_human_precharge_costs,
            "credits": current_user.credits,
        }
    )


@router.post("/orders", response_model=Response)
async def create_order(
    req: CreateOrderRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        packages = await get_effective_recharge_packages(db)
        package = next((item for item in packages if item["id"] == req.package_id), None)
        if not package:
            return fail("充值套餐不存在或已下架")
        pid = _zpay_pid()
        key = _zpay_key()
        gateway = _zpay_gateway()
        notify_url = _zpay_notify_url()
        return_url = _zpay_return_url()
    except ValueError as exc:
        return fail(str(exc))

    out_trade_no = _make_out_trade_no()
    order = CreditOrder(
        user_id=current_user.id,
        out_trade_no=out_trade_no,
        package_id=package["id"],
        package_name=package["name"],
        package_snapshot_json=dump_json(package),
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
        return fail("创建充值订单失败，请稍后重试")

    payload: dict[str, Any] = {
        "pid": pid,
        "type": "wxpay",
        "out_trade_no": out_trade_no,
        "notify_url": notify_url,
        "return_url": return_url,
        "name": f"商图AI积分充值-{package['name']}",
        "money": _format_amount(package["amount_cents"]),
        "clientip": _client_ip(request),
        "device": "pc",
        "param": order.id,
        "sign_type": "MD5",
    }
    payload["sign"] = zpay_sign(payload, key)

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{gateway}/mapi.php",
                data=payload,
            )
            data = response.json()
    except Exception:
        order.status = "failed"
        order.error_message = "支付订单创建失败"
        order.updated_at = utc_now()
        await db.commit()
        return fail("支付订单创建失败，请稍后重试", data=_order_payload(order))

    if str(data.get("code")) != "1":
        order.status = "failed"
        order.error_message = str(data.get("msg") or "支付订单创建失败")
        order.updated_at = utc_now()
        await db.commit()
        return fail(order.error_message, data=_order_payload(order))

    order.provider_trade_no = str(data.get("trade_no") or data.get("O_id") or "") or None
    order.pay_url = data.get("payurl") or None
    order.qr_code = data.get("qrcode") or None
    order.qr_img = data.get("img") or None
    order.updated_at = utc_now()
    await db.commit()
    await db.refresh(order)
    return success(_order_payload(order))


@router.get("/orders/{order_id}", response_model=Response)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CreditOrder).where(
            CreditOrder.id == order_id,
            CreditOrder.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        return fail("订单不存在")
    latest_user = await db.get(User, current_user.id)
    return success(_order_payload(order, credits=latest_user.credits if latest_user else None))


@router.get("/zpay/notify", response_class=PlainTextResponse)
async def zpay_notify(request: Request, db: AsyncSession = Depends(get_db)):
    params = dict(request.query_params)
    try:
        key = _zpay_key()
        pid = _zpay_pid()
    except ValueError:
        return PlainTextResponse("fail")

    sign = params.get("sign")
    if not sign or sign.lower() != zpay_sign(params, key):
        return PlainTextResponse("fail")
    if str(params.get("pid") or "") != str(pid):
        return PlainTextResponse("fail")
    if params.get("trade_status") != "TRADE_SUCCESS":
        return PlainTextResponse("success")

    out_trade_no = params.get("out_trade_no")
    if not out_trade_no:
        return PlainTextResponse("fail")
    notify_amount_cents = _parse_amount_cents(params.get("money"))
    if notify_amount_cents is None:
        return PlainTextResponse("fail")

    async with db.begin():
        result = await db.execute(
            select(CreditOrder)
            .where(CreditOrder.out_trade_no == out_trade_no)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            return PlainTextResponse("fail")
        if notify_amount_cents != order.amount_cents:
            order.error_message = "支付回调金额不一致"
            order.updated_at = utc_now()
            return PlainTextResponse("fail")
        if order.status == "paid":
            return PlainTextResponse("success")

        user_result = await db.execute(
            select(User).where(User.id == order.user_id).with_for_update()
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return PlainTextResponse("fail")

        trade_no = params.get("trade_no")
        order.status = "paid"
        order.provider_trade_no = trade_no or order.provider_trade_no
        order.paid_at = utc_now()
        order.updated_at = order.paid_at
        user.credits += order.credits
        balance_after = user.credits
        db.add(
            CreditTransaction(
                user_id=user.id,
                order_id=order.id,
                type="recharge",
                credits_delta=order.credits,
                balance_after=balance_after,
                note=f"{order.package_name} 充值到账",
            )
        )

    return PlainTextResponse("success")


@router.get("/zpay/return", response_class=HTMLResponse)
async def zpay_return():
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="zh-CN">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>支付结果处理中</title>
            <style>
              body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f8fafc; color: #0f172a; }
              main { min-height: 100vh; display: grid; place-items: center; padding: 24px; box-sizing: border-box; }
              section { width: min(420px, 100%); border: 1px solid #e2e8f0; border-radius: 16px; background: white; padding: 28px; text-align: center; box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08); }
              h1 { margin: 0 0 10px; font-size: 20px; }
              p { margin: 0; color: #64748b; line-height: 1.7; font-size: 14px; }
            </style>
          </head>
          <body>
            <main>
              <section>
                <h1>支付结果处理中</h1>
                <p>请回到商图页面查看积分到账状态。积分到账只以后端异步通知为准，通常几秒内会自动刷新。</p>
              </section>
            </main>
          </body>
        </html>
        """
    )
