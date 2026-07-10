from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.time import utc_now
from app.models import CreditOrder, ImageTask, User, VideoTask
from app.schemas.response import Response, success

router = APIRouter()


@router.get("/overview", response_model=Response)
async def overview(
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    total_users = await db.scalar(select(func.count()).select_from(User))
    active_users = await db.scalar(
        select(func.count()).select_from(User).where(User.status == "active")
    )
    disabled_users = await db.scalar(
        select(func.count()).select_from(User).where(User.status == "disabled")
    )
    super_admins = await db.scalar(
        select(func.count()).select_from(User).where(User.role == "super_admin")
    )
    today_new_users = await db.scalar(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    )
    total_credit_balance = await db.scalar(select(func.coalesce(func.sum(User.credits), 0)))
    paid_amount_cents = await db.scalar(
        select(func.coalesce(func.sum(CreditOrder.amount_cents), 0)).where(
            CreditOrder.status == "paid"
        )
    )
    today_paid_amount_cents = await db.scalar(
        select(func.coalesce(func.sum(CreditOrder.amount_cents), 0)).where(
            CreditOrder.status == "paid",
            CreditOrder.paid_at >= today_start,
        )
    )
    today_image_tasks = await db.scalar(
        select(func.count()).select_from(ImageTask).where(ImageTask.created_at >= today_start)
    )
    today_video_tasks = await db.scalar(
        select(func.count()).select_from(VideoTask).where(VideoTask.created_at >= today_start)
    )
    failed_image_tasks = await db.scalar(
        select(func.count())
        .select_from(ImageTask)
        .where(ImageTask.status.in_(["failed", "timeout"]))
    )
    failed_video_tasks = await db.scalar(
        select(func.count())
        .select_from(VideoTask)
        .where(VideoTask.status.in_(["failed", "timeout"]))
    )
    return success(
        {
            "total_users": int(total_users or 0),
            "active_users": int(active_users or 0),
            "disabled_users": int(disabled_users or 0),
            "super_admins": int(super_admins or 0),
            "today_new_users": int(today_new_users or 0),
            "total_credit_balance": int(total_credit_balance or 0),
            "paid_amount_cents": int(paid_amount_cents or 0),
            "today_paid_amount_cents": int(today_paid_amount_cents or 0),
            "today_tasks": int(today_image_tasks or 0) + int(today_video_tasks or 0),
            "failed_tasks": int(failed_image_tasks or 0) + int(failed_video_tasks or 0),
        }
    )
