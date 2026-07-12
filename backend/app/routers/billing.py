from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.system_settings import get_effective_recharge_packages
from app.core.time import to_utc_iso
from app.models import CreditOrder, User
from app.schemas.response import Response, fail, success
from app.services.billing import create_credit_order, process_zpay_notification

router = APIRouter(prefix="/billing", tags=["积分充值"])

class CreateOrderRequest(BaseModel):
    package_id: str


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


@router.get("/packages", response_model=Response)
async def list_packages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        packages = await get_effective_recharge_packages(db)
    except ValueError as exc:
        return fail(str(exc))
    return success(
        {
            "packages": packages,
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
    outcome = await create_credit_order(
        db=db,
        current_user=current_user,
        package_id=req.package_id,
        client_ip=_client_ip(request),
    )
    if outcome.error_message:
        data = _order_payload(outcome.order) if outcome.order else None
        return fail(outcome.error_message, data=data)
    return success(_order_payload(outcome.order))


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
    result = await process_zpay_notification(db, dict(request.query_params))
    return PlainTextResponse(result)


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
