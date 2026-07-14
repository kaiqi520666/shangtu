import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import task_log_extra
from app.core.user_credits import (
    CreditCharge,
    calculate_user_credit_cost,
    charge_user_credits,
    get_user_credits,
    insufficient_credits_message,
)
from app.models import User
from app.schemas.response import Response, fail

logger = logging.getLogger("app.services.generation_tasks")

FailureMarker = Callable[[int], Awaitable[None]]
BeforeEnqueue = Callable[[Any], Awaitable[None]]
RefundCredits = Callable[[AsyncSession, int, int, str | None], Awaitable[int]]
RedisPoolGetter = Callable[[], Any]


async def deduct_credits_or_fail(
    db: AsyncSession,
    user_id: int,
    cost: int,
    note: str | None = None,
) -> tuple[CreditCharge | None, Response | None]:
    user = await db.get(User, user_id)
    required = calculate_user_credit_cost(cost, user.consumption_multiplier)
    charge = await charge_user_credits(db, user_id, cost, note=note)
    if charge is None:
        await db.rollback()
        latest_credits = await get_user_credits(db, user_id)
        return None, fail(insufficient_credits_message(required, latest_credits))
    return charge, None


async def enqueue_or_compensate(
    *,
    get_redis_pool: RedisPoolGetter,
    db: AsyncSession,
    job_name: str,
    job_args: Sequence[Any],
    user_id: int,
    credit_cost: int,
    remaining_credits: int,
    refund_credits: RefundCredits,
    mark_failed: FailureMarker,
    failure_message: str,
    failure_data: dict[str, Any],
    refund_note: str | None = None,
    before_enqueue: BeforeEnqueue | None = None,
) -> Response | None:
    try:
        redis_pool = get_redis_pool()
        if before_enqueue is not None:
            await before_enqueue(redis_pool)
        await redis_pool.enqueue_job(job_name, *job_args)
    except Exception:
        logger.warning(
            "Generation enqueue failed; starting compensation job=%s user_id=%s cost=%s",
            job_name,
            user_id,
            credit_cost,
            exc_info=True,
            extra=task_log_extra(
                event="generation_enqueue_failed",
                task_id=failure_data.get("task_id"),
                job_id=failure_data.get("job_id"),
                phase="enqueue",
                status="failed",
            ),
        )
        try:
            refunded_credits = await refund_credits(db, user_id, credit_cost, refund_note)
            await mark_failed(refunded_credits)
            await db.commit()
        except Exception:
            await db.rollback()
            refunded_credits = remaining_credits
            logger.error(
                "Generation compensation failed job=%s user_id=%s cost=%s; "
                "credits and task state may be inconsistent",
                job_name,
                user_id,
                credit_cost,
                exc_info=True,
                extra=task_log_extra(
                    event="generation_compensation_failed",
                    task_id=failure_data.get("task_id"),
                    job_id=failure_data.get("job_id"),
                    phase="compensation",
                    status="failed",
                ),
            )
        return fail(
            failure_message,
            data={
                **failure_data,
                "credits": refunded_credits,
                "credit_cost": credit_cost,
            },
        )
    return None
