from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commissions import add_wallet_transaction, commission_transaction_payload, withdrawal_payload
from app.core.deps import get_current_user, get_db
from app.core.pagination import page_payload
from app.core.time import to_utc_iso
from app.models import CommissionTransaction, CommissionWithdrawal, CreditOrder, CreditTransaction, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/account/distribution", tags=["分销中心"])


class UpdateDownlineRateRequest(BaseModel):
    commission_rate: Decimal = Field(..., ge=Decimal("0"), le=Decimal("100"), decimal_places=2)


class CreateWithdrawalRequest(BaseModel):
    amount_cents: int = Field(..., ge=10000)
    alipay_name: str = Field(..., min_length=1, max_length=100)
    alipay_account: str = Field(..., min_length=1, max_length=150)


def _require_distribution(user: User):
    if not user.distribution_level or not user.distribution_enabled:
        return fail("分销功能未启用")
    return None


async def _downline_payload(db: AsyncSession, viewer: User, user: User) -> dict:
    source_ids = [user.id]
    commission_source_ids = [user.id]
    if viewer.distribution_level == 1 and user.distribution_level == 2:
        commission_source_ids.extend(
            (await db.execute(select(User.id).where(User.distribution_parent_id == user.id))).scalars()
        )
    recharge = await db.scalar(
        select(func.coalesce(func.sum(CreditOrder.amount_cents), 0)).where(
            CreditOrder.user_id.in_(source_ids), CreditOrder.status == "paid"
        )
    )
    consumed = await db.scalar(
        select(func.coalesce(func.sum(-CreditTransaction.credits_delta), 0)).where(
            CreditTransaction.user_id.in_(source_ids), CreditTransaction.type == "consume"
        )
    )
    contribution = await db.scalar(
        select(func.coalesce(func.sum(CommissionTransaction.available_delta_cents), 0)).where(
            CommissionTransaction.user_id == viewer.id,
            CommissionTransaction.source_user_id.in_(commission_source_ids),
            CommissionTransaction.type == "earning",
        )
    )
    local, _, domain = user.email.partition("@")
    return {
        "id": user.id,
        "username": user.username,
        "email": f"{local[:2]}***@{domain}" if domain else "***",
        "level": user.distribution_level,
        "commission_rate": float(user.commission_rate or 0),
        "recharge_cents": int(recharge or 0),
        "consumed_credits": int(consumed or 0),
        "contributed_commission_cents": int(contribution or 0),
        "created_at": to_utc_iso(user.created_at),
    }


@router.get("/overview", response_model=Response)
async def overview(current_user: User = Depends(get_current_user)):
    failure = _require_distribution(current_user)
    if failure:
        return failure
    return success(
        {
            "level": current_user.distribution_level,
            "commission_rate": float(current_user.commission_rate or 0),
            "invite_code": current_user.invite_code,
            "commission_available_cents": current_user.commission_available_cents,
            "commission_frozen_cents": current_user.commission_frozen_cents,
            "commission_withdrawn_cents": current_user.commission_withdrawn_cents,
        }
    )


@router.get("/downlines", response_model=Response)
async def downlines(
    page: int = 1,
    page_size: int = 20,
    level: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    failure = _require_distribution(current_user)
    if failure:
        return failure
    page, page_size = max(1, page), min(max(1, page_size), 100)
    direct_ids = list(
        (await db.execute(select(User.id).where(User.distribution_parent_id == current_user.id))).scalars()
    )
    conditions = [User.distribution_parent_id == current_user.id]
    if current_user.distribution_level == 1 and level != 2:
        conditions = [or_(User.distribution_parent_id == current_user.id, User.distribution_parent_id.in_(direct_ids))]
    if level in {2, 3}:
        conditions.append(User.distribution_level == level)
    total = int((await db.scalar(select(func.count()).select_from(User).where(*conditions))) or 0)
    users = (
        await db.execute(
            select(User)
            .where(*conditions)
            .order_by(User.distribution_level, User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    items = [await _downline_payload(db, current_user, user) for user in users]
    return success(page_payload(items, total, page, page_size))


@router.patch("/downlines/{user_id}/rate", response_model=Response)
async def update_downline_rate(
    user_id: int,
    req: UpdateDownlineRateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    failure = _require_distribution(current_user)
    if failure:
        return failure
    target = (
        await db.execute(select(User).where(User.id == user_id).with_for_update())
    ).scalar_one_or_none()
    if not target or target.distribution_parent_id != current_user.id:
        return fail("只能设置直接下级的分销比例")
    if req.commission_rate > current_user.commission_rate:
        return fail("下级比例不能超过自身比例")
    max_child_rate = await db.scalar(
        select(func.max(User.commission_rate)).where(User.distribution_parent_id == target.id)
    )
    if max_child_rate is not None and req.commission_rate < max_child_rate:
        return fail("当前比例不能低于已有下级比例")
    target.commission_rate = req.commission_rate
    await db.commit()
    return success({"user_id": target.id, "commission_rate": float(target.commission_rate)})


@router.get("/transactions", response_model=Response)
async def transactions(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    failure = _require_distribution(current_user)
    if failure:
        return failure
    page, page_size = max(1, page), min(max(1, page_size), 100)
    condition = CommissionTransaction.user_id == current_user.id
    total = int((await db.scalar(select(func.count()).select_from(CommissionTransaction).where(condition))) or 0)
    rows = (
        await db.execute(
            select(CommissionTransaction)
            .where(condition)
            .order_by(CommissionTransaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return success(page_payload([commission_transaction_payload(item) for item in rows], total, page, page_size))


@router.get("/withdrawals", response_model=Response)
async def withdrawals(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    failure = _require_distribution(current_user)
    if failure:
        return failure
    page, page_size = max(1, page), min(max(1, page_size), 100)
    condition = CommissionWithdrawal.user_id == current_user.id
    total = int((await db.scalar(select(func.count()).select_from(CommissionWithdrawal).where(condition))) or 0)
    rows = (
        await db.execute(
            select(CommissionWithdrawal)
            .where(condition)
            .order_by(CommissionWithdrawal.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return success(page_payload([withdrawal_payload(item) for item in rows], total, page, page_size))


@router.post("/withdrawals", response_model=Response)
async def create_withdrawal(
    req: CreateWithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.amount_cents % 10000:
        return fail("提现金额必须是 100 元的整数倍")
    if not req.alipay_name.strip() or not req.alipay_account.strip():
        return fail("请填写支付宝姓名和账号")
    user = (
        await db.execute(select(User).where(User.id == current_user.id).with_for_update())
    ).scalar_one()
    failure = _require_distribution(user)
    if failure:
        return failure
    if user.commission_available_cents < req.amount_cents:
        return fail("可提现余额不足")
    item = CommissionWithdrawal(
        user_id=user.id,
        amount_cents=req.amount_cents,
        alipay_name=req.alipay_name.strip(),
        alipay_account=req.alipay_account.strip(),
    )
    db.add(item)
    await db.flush()
    user.commission_available_cents -= req.amount_cents
    user.commission_frozen_cents += req.amount_cents
    add_wallet_transaction(
        db,
        user,
        tx_type="withdraw_freeze",
        available_delta=-req.amount_cents,
        frozen_delta=req.amount_cents,
        withdrawal_id=item.id,
        note="提交佣金提现",
    )
    await db.commit()
    await db.refresh(item)
    return success(withdrawal_payload(item))
