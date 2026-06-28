from typing import Any

from sqlalchemy import select, update

from app.core.database import SessionLocal


def task_model(media_type: str):
    from app.models import ImageTask, VideoTask

    return ImageTask if media_type == "image" else VideoTask


async def update_generation_task_in_db(
    media_type: str,
    task_id: str,
    *,
    status: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    provider_task_id: str | None = None,
) -> None:
    model = task_model(media_type)

    values: dict[str, Any] = {}
    if status is not None:
        values["status"] = status
    if result_url is not None:
        values["result_url"] = result_url
    if error_message is not None:
        values["error_message"] = error_message
    if progress is not None:
        values["progress"] = max(0, min(100, int(progress)))
    if provider_task_id is not None:
        values["provider_task_id"] = provider_task_id

    if not values:
        return

    async with SessionLocal() as session:
        await session.execute(
            update(model)
            .where(model.id == task_id)
            .values(**values)
        )
        await session.commit()


async def update_task_in_db(
    task_id: str,
    *,
    status: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    provider_task_id: str | None = None,
) -> None:
    await update_generation_task_in_db(
        "image",
        task_id,
        status=status,
        result_url=result_url,
        error_message=error_message,
        progress=progress,
        provider_task_id=provider_task_id,
    )


async def update_video_task_in_db(
    task_id: str,
    *,
    status: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    provider_task_id: str | None = None,
) -> None:
    await update_generation_task_in_db(
        "video",
        task_id,
        status=status,
        result_url=result_url,
        error_message=error_message,
        progress=progress,
        provider_task_id=provider_task_id,
    )


async def fetch_generation_task_user_id(media_type: str, task_id: str) -> int | None:
    model = task_model(media_type)

    async with SessionLocal() as session:
        result = await session.execute(
            select(model.user_id).where(model.id == task_id)
        )
        return result.scalar_one_or_none()


async def fetch_task_user_id(task_id: str) -> int | None:
    return await fetch_generation_task_user_id("image", task_id)


async def fetch_video_task_user_id(task_id: str) -> int | None:
    return await fetch_generation_task_user_id("video", task_id)


async def refund_generation_credit(media_type: str, task_id: str) -> bool:
    """幂等退款：按任务实际扣费退回积分，已退过直接 no-op。返回是否本次执行了退款。"""
    from app.models import User

    model = task_model(media_type)

    async with SessionLocal() as session:
        async with session.begin():
            task_row = await session.execute(
                select(
                    model.user_id,
                    model.credit_cost,
                    model.credit_refunded,
                ).where(model.id == task_id).with_for_update()
            )
            row = task_row.first()
            if not row:
                return False
            user_id, credit_cost, refunded = row
            if refunded:
                return False
            refund_amount = max(1, int(credit_cost or 1))
            await session.execute(
                update(User).where(User.id == user_id).values(
                    credits=User.credits + refund_amount
                )
            )
            await session.execute(
                update(model).where(model.id == task_id).values(
                    credit_refunded=True
                )
            )
    return True
