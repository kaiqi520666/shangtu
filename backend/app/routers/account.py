from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import set_user_password, validate_password, verify_password
from app.core.credit_transactions import transaction_payload
from app.core.coupons import normalize_coupon_code, redeem_coupon
from app.core.deps import get_current_user, get_db
from app.core.pagination import page_payload
from app.core.time import to_utc_iso
from app.models import CreditTransaction, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/account", tags=["账号中心"])


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class RedeemCouponRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return normalize_coupon_code(value)


def account_profile_payload(user: User) -> dict:
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "credits": user.credits,
        "consumption_multiplier": float(user.consumption_multiplier),
        "distribution_level": user.distribution_level,
        "distribution_enabled": user.distribution_enabled,
        "role": user.role,
        "status": user.status,
        "created_at": to_utc_iso(user.created_at),
    }


@router.get("/profile", response_model=Response)
async def account_profile(current_user: User = Depends(get_current_user)):
    return success(account_profile_payload(current_user))


@router.put("/password", response_model=Response)
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (
        await db.execute(select(User).where(User.id == current_user.id).with_for_update())
    ).scalar_one()
    if not verify_password(req.current_password, user.password_hash):
        return fail("当前密码错误")
    try:
        validate_password(req.new_password)
    except ValueError as exc:
        return fail(str(exc))
    if req.new_password == req.current_password:
        return fail("新密码不能与当前密码相同")
    set_user_password(user, req.new_password)
    await db.commit()
    return success(message="密码已修改，请重新登录")


@router.post("/coupon-redemptions", response_model=Response)
async def redeem_coupon_code(
    req: RedeemCouponRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        coupon, user = await redeem_coupon(db, current_user.id, req.code)
    except ValueError as exc:
        return fail(str(exc))
    await db.commit()
    return success(
        {
            "code": coupon.code,
            "credits_added": coupon.credits,
            "credits": user.credits,
        },
        message="优惠码兑换成功",
    )


@router.get("/credit-transactions", response_model=Response)
async def list_account_credit_transactions(
    page: int = 1,
    page_size: int = 20,
    type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = [CreditTransaction.user_id == current_user.id]
    if type in {"recharge", "consume", "refund", "admin_adjust", "coupon_redeem"}:
        conditions.append(CreditTransaction.type == type)

    total_stmt = select(func.count()).select_from(CreditTransaction).where(*conditions)
    data_stmt = (
        select(CreditTransaction)
        .where(*conditions)
        .order_by(CreditTransaction.created_at.desc())
    )
    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [transaction_payload(tx) for tx in result.scalars().all()]
    return success(page_payload(items, total, page, page_size))
