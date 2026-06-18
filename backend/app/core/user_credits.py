from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_user_credits(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(select(User.credits).where(User.id == user_id))
    return int(result.scalar_one_or_none() or 0)


def insufficient_credits_message(required: int, available: int) -> str:
    return f"积分不足，本次需要 {required} 点，当前剩余 {max(0, available)} 点"


async def deduct_user_credits(db: AsyncSession, user_id: int, cost: int) -> int | None:
    result = await db.execute(
        update(User)
        .where(User.id == user_id, User.credits >= cost)
        .values(credits=User.credits - cost)
        .returning(User.credits)
        .execution_options(synchronize_session=False)
    )
    value = result.scalar_one_or_none()
    return int(value) if value is not None else None


async def refund_user_credits(db: AsyncSession, user_id: int, cost: int) -> int:
    result = await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(credits=User.credits + cost)
        .returning(User.credits)
        .execution_options(synchronize_session=False)
    )
    return int(result.scalar_one())
