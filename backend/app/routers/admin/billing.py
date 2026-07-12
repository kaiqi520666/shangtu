from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.models import CreditOrder, CreditTransaction, User
from app.schemas.response import Response, success

from .utils import order_payload, page_payload, transaction_payload

router = APIRouter()


@router.get("/credit-orders", response_model=Response)
async def list_credit_orders(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = []
    if status in {"pending", "paid", "failed"}:
        conditions.append(CreditOrder.status == status)
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                CreditOrder.out_trade_no.ilike(like),
                CreditOrder.provider_trade_no.ilike(like),
                User.email.ilike(like),
            )
        )
    total_stmt = (
        select(func.count())
        .select_from(CreditOrder)
        .join(User, User.id == CreditOrder.user_id)
    )
    data_stmt = (
        select(CreditOrder, User)
        .join(User, User.id == CreditOrder.user_id)
        .order_by(CreditOrder.created_at.desc())
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)
    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [order_payload(order, user) for order, user in result.all()]
    return success(page_payload(items, total, page, page_size))


@router.get("/credit-transactions", response_model=Response)
async def list_credit_transactions(
    page: int = 1,
    page_size: int = 20,
    type: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = []
    if type in {"recharge", "consume", "refund", "admin_adjust", "coupon_redeem"}:
        conditions.append(CreditTransaction.type == type)
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(or_(User.email.ilike(like), CreditTransaction.note.ilike(like)))
    total_stmt = (
        select(func.count())
        .select_from(CreditTransaction)
        .join(User, User.id == CreditTransaction.user_id)
    )
    data_stmt = (
        select(CreditTransaction, User)
        .join(User, User.id == CreditTransaction.user_id)
        .order_by(CreditTransaction.created_at.desc())
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)
    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [transaction_payload(tx, user) for tx, user in result.all()]
    return success(page_payload(items, total, page, page_size))
