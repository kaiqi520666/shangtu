from __future__ import annotations

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.database import SessionLocal, engine  # noqa: E402
from app.core.providers.zpay import (  # noqa: E402
    format_amount,
    get_zpay_key,
    get_zpay_pid,
    sign_params,
)
from app.models import CreditOrder  # noqa: E402

load_dotenv()


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("用法: python scripts/simulate_zpay_notify.py <out_trade_no>")

    out_trade_no = sys.argv[1]
    async with SessionLocal() as db:
        result = await db.execute(
            select(CreditOrder).where(CreditOrder.out_trade_no == out_trade_no)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise SystemExit(f"订单不存在: {out_trade_no}")

        params = {
            "pid": get_zpay_pid(),
            "name": f"商图AI积分充值-{order.package_name}",
            "money": format_amount(order.amount_cents),
            "out_trade_no": order.out_trade_no,
            "trade_no": f"SIM{order.out_trade_no}",
            "param": order.id,
            "trade_status": "TRADE_SUCCESS",
            "type": order.pay_type,
            "sign_type": "MD5",
        }
        params["sign"] = sign_params(params, get_zpay_key())

    base_url = os.getenv("LOCAL_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{base_url}/billing/zpay/notify", params=params)
        print(response.text)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
