import json
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.time import to_utc_iso, utc_now
from app.models import AdminAuditLog, CreditOrder, CreditTransaction, ImageTask, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/admin", tags=["管理后台"])

RoleValue = Literal["user", "super_admin"]
StatusValue = Literal["active", "disabled"]


class UpdateUserRequest(BaseModel):
    role: RoleValue | None = None
    status: StatusValue | None = None


class AdjustCreditsRequest(BaseModel):
    amount: int = Field(..., ge=-1000000, le=1000000)
    note: str = Field(..., min_length=1, max_length=255)


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "credits": user.credits,
        "role": user.role,
        "status": user.status,
        "disabled_at": to_utc_iso(user.disabled_at),
        "created_at": to_utc_iso(user.created_at),
    }


def _order_payload(order: CreditOrder, user: User | None = None) -> dict:
    return {
        "id": order.id,
        "user_id": order.user_id,
        "user_email": user.email if user else None,
        "out_trade_no": order.out_trade_no,
        "provider_trade_no": order.provider_trade_no,
        "package_id": order.package_id,
        "package_name": order.package_name,
        "credits": order.credits,
        "amount_cents": order.amount_cents,
        "pay_type": order.pay_type,
        "status": order.status,
        "error_message": order.error_message,
        "created_at": to_utc_iso(order.created_at),
        "paid_at": to_utc_iso(order.paid_at),
    }


def _transaction_payload(tx: CreditTransaction, user: User | None = None) -> dict:
    return {
        "id": tx.id,
        "user_id": tx.user_id,
        "user_email": user.email if user else None,
        "order_id": tx.order_id,
        "type": tx.type,
        "credits_delta": tx.credits_delta,
        "balance_after": tx.balance_after,
        "note": tx.note,
        "created_at": to_utc_iso(tx.created_at),
    }


def _page_payload(items: list[dict], total: int, page: int, page_size: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def _audit_log(
    actor: User,
    action: str,
    target_type: str,
    target_id: str,
    detail: dict | None = None,
) -> AdminAuditLog:
    return AdminAuditLog(
        actor_user_id=actor.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail_json=json.dumps(detail or {}, ensure_ascii=False),
    )


async def _super_admin_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.role == "super_admin", User.status == "active")
    )
    return int(result.scalar_one() or 0)


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
    failed_image_tasks = await db.scalar(
        select(func.count())
        .select_from(ImageTask)
        .where(ImageTask.status.in_(["failed", "timeout"]))
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
            "today_image_tasks": int(today_image_tasks or 0),
            "failed_image_tasks": int(failed_image_tasks or 0),
        }
    )


@router.get("/users", response_model=Response)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    role: str | None = None,
    status: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = []
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(or_(User.email.ilike(like), User.username.ilike(like)))
    if role in {"user", "super_admin"}:
        conditions.append(User.role == role)
    if status in {"active", "disabled"}:
        conditions.append(User.status == status)

    total_stmt = select(func.count()).select_from(User)
    data_stmt = select(User).order_by(User.created_at.desc(), User.id.desc())
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)
    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    users = result.scalars().all()
    return success(_page_payload([_user_payload(user) for user in users], total, page, page_size))


@router.patch("/users/{user_id}", response_model=Response)
async def update_user(
    user_id: int,
    req: UpdateUserRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if not target:
        return fail("用户不存在")
    old_role = target.role
    old_status = target.status

    if req.status == "disabled" and target.id == current_admin.id:
        return fail("不能禁用当前登录的超级管理员")
    if req.role == "user" and target.id == current_admin.id:
        return fail("不能取消当前登录账号的超级管理员权限")

    would_remove_active_super_admin = (
        target.role == "super_admin"
        and target.status == "active"
        and (req.role == "user" or req.status == "disabled")
    )
    if would_remove_active_super_admin and await _super_admin_count(db) <= 1:
        return fail("至少需要保留一个可用的超级管理员")

    changed = False
    if req.role and req.role != target.role:
        target.role = req.role
        changed = True
    if req.status and req.status != target.status:
        target.status = req.status
        target.disabled_at = utc_now() if req.status == "disabled" else None
        changed = True

    if not changed:
        return success(_user_payload(target))

    db.add(
        _audit_log(
            current_admin,
            "update_user",
            "user",
            str(target.id),
            {
                "old_role": old_role,
                "new_role": target.role,
                "old_status": old_status,
                "new_status": target.status,
            },
        )
    )
    await db.commit()
    await db.refresh(target)
    return success(_user_payload(target))


@router.post("/users/{user_id}/credits/adjust", response_model=Response)
async def adjust_user_credits(
    user_id: int,
    req: AdjustCreditsRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    if req.amount == 0:
        return fail("调整积分不能为 0")
    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    target = result.scalar_one_or_none()
    if not target:
        return fail("用户不存在")
    if target.credits + req.amount < 0:
        return fail("扣减后积分不能小于 0")

    old_credits = target.credits
    target.credits += req.amount
    tx = CreditTransaction(
        user_id=target.id,
        order_id=None,
        type="admin_adjust",
        credits_delta=req.amount,
        balance_after=target.credits,
        note=req.note.strip(),
    )
    db.add(tx)
    db.add(
        _audit_log(
            current_admin,
            "adjust_credits",
            "user",
            str(target.id),
            {
                "amount": req.amount,
                "old_credits": old_credits,
                "new_credits": target.credits,
                "note": req.note.strip(),
            },
        )
    )
    await db.commit()
    await db.refresh(target)
    return success(_user_payload(target))


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
    total_stmt = select(func.count()).select_from(CreditOrder).join(User, User.id == CreditOrder.user_id)
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
    items = [_order_payload(order, user) for order, user in result.all()]
    return success(_page_payload(items, total, page, page_size))


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
    if type in {"recharge", "consume", "refund", "admin_adjust"}:
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
    items = [_transaction_payload(tx, user) for tx, user in result.all()]
    return success(_page_payload(items, total, page, page_size))
