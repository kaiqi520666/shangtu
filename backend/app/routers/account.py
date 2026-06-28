from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credit_transactions import transaction_payload
from app.core.deps import get_current_user, get_db
from app.core.pagination import page_payload
from app.core.time import to_utc_iso
from app.models import CreditTransaction, User
from app.schemas.response import Response, success

router = APIRouter(prefix="/account", tags=["账号中心"])


def account_profile_payload(user: User) -> dict:
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "credits": user.credits,
        "role": user.role,
        "status": user.status,
        "created_at": to_utc_iso(user.created_at),
    }


@router.get("/profile", response_model=Response)
async def account_profile(current_user: User = Depends(get_current_user)):
    return success(account_profile_payload(current_user))


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
    if type in {"recharge", "consume", "refund", "admin_adjust"}:
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
