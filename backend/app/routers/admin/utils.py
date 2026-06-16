import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import to_utc_iso
from app.models import AdminAuditLog, CreditOrder, CreditTransaction, User


def user_payload(user: User) -> dict:
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


def order_payload(order: CreditOrder, user: User | None = None) -> dict:
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


def transaction_payload(tx: CreditTransaction, user: User | None = None) -> dict:
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


def page_payload(items: list[dict], total: int, page: int, page_size: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def audit_log(
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


async def super_admin_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.role == "super_admin", User.status == "active")
    )
    return int(result.scalar_one() or 0)
