import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CouponCode, CouponRedemption, CreditTransaction, User

COUPON_CODE_PATTERN = re.compile(r"^[A-Z0-9-]{4,32}$")


def normalize_coupon_code(value: str) -> str:
    code = value.strip().upper()
    if not COUPON_CODE_PATTERN.fullmatch(code):
        raise ValueError("优惠码只能包含 4～32 位大写字母、数字或连字符")
    return code


async def redeem_coupon(
    db: AsyncSession,
    user_id: int,
    code: str,
) -> tuple[CouponCode, User]:
    coupon = (
        await db.execute(
            select(CouponCode).where(CouponCode.code == code).with_for_update()
        )
    ).scalar_one_or_none()
    if not coupon or coupon.deleted_at is not None:
        raise ValueError("优惠码不存在或已删除")
    if not coupon.enabled:
        raise ValueError("优惠码已停用")
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise ValueError("优惠码使用次数已用完")
    redeemed = await db.scalar(
        select(CouponRedemption.id).where(
            CouponRedemption.coupon_code_id == coupon.id,
            CouponRedemption.user_id == user_id,
        )
    )
    if redeemed:
        raise ValueError("你已经兑换过该优惠码")

    user = (
        await db.execute(select(User).where(User.id == user_id).with_for_update())
    ).scalar_one()
    user.credits += coupon.credits
    coupon.used_count += 1
    transaction = CreditTransaction(
        user_id=user.id,
        order_id=None,
        type="coupon_redeem",
        credits_delta=coupon.credits,
        balance_after=user.credits,
        note=f"优惠码兑换：{coupon.code}",
    )
    db.add(transaction)
    await db.flush()
    db.add(
        CouponRedemption(
            coupon_code_id=coupon.id,
            user_id=user.id,
            code_snapshot=coupon.code,
            credits_snapshot=coupon.credits,
            credit_transaction_id=transaction.id,
        )
    )
    return coupon, user
