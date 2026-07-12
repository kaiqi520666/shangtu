from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CreditTransaction, User


async def get_user_credits(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(select(User.credits).where(User.id == user_id))
    return int(result.scalar_one_or_none() or 0)


def insufficient_credits_message(required: int, available: int) -> str:
    return f"积分不足，本次需要 {required} 点，当前剩余 {max(0, available)} 点"


def _trim_note(note: str | None) -> str | None:
    if not note:
        return None
    return note.strip()[:255] or None


def add_credit_transaction(
    db: AsyncSession,
    *,
    user_id: int,
    tx_type: str,
    credits_delta: int,
    balance_after: int,
    note: str | None = None,
    order_id: str | None = None,
) -> None:
    db.add(
        CreditTransaction(
            user_id=user_id,
            order_id=order_id,
            type=tx_type,
            credits_delta=credits_delta,
            balance_after=balance_after,
            note=_trim_note(note),
        )
    )


@dataclass(frozen=True)
class CreditCharge:
    cost: int
    balance_after: int
    multiplier: Decimal


def calculate_user_credit_cost(base_cost: int, multiplier: Decimal | str | float) -> int:
    return int(
        (Decimal(int(base_cost)) * Decimal(str(multiplier))).to_integral_value(
            rounding=ROUND_CEILING
        )
    )


async def charge_user_credits(
    db: AsyncSession,
    user_id: int,
    base_cost: int,
    note: str | None = None,
    *,
    multiplier: Decimal | str | float | None = None,
    allow_negative: bool = False,
) -> CreditCharge | None:
    user = (
        await db.execute(select(User).where(User.id == user_id).with_for_update())
    ).scalar_one()
    applied_multiplier = Decimal(str(multiplier or user.consumption_multiplier))
    cost = calculate_user_credit_cost(base_cost, applied_multiplier)
    if not allow_negative and user.credits < cost:
        return None
    user.credits -= cost
    add_credit_transaction(
        db,
        user_id=user_id,
        tx_type="consume",
        credits_delta=-cost,
        balance_after=user.credits,
        note=note,
    )
    return CreditCharge(
        cost=cost,
        balance_after=user.credits,
        multiplier=applied_multiplier,
    )


async def refund_user_credits(
    db: AsyncSession,
    user_id: int,
    cost: int,
    note: str | None = None,
) -> int:
    result = await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(credits=User.credits + cost)
        .returning(User.credits)
        .execution_options(synchronize_session=False)
    )
    balance_after = int(result.scalar_one())
    add_credit_transaction(
        db,
        user_id=user_id,
        tx_type="refund",
        credits_delta=abs(int(cost)),
        balance_after=balance_after,
        note=note,
    )
    return balance_after
