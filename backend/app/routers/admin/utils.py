import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import parse_json_or_none
from app.core.task_timeout import user_visible_task_error
from app.core.time import to_utc_iso
from app.models import (
    AdminAuditLog,
    CreditOrder,
    CreditTransaction,
    GenerationJob,
    ImageTask,
    OutfitModel,
    PromptTemplate,
    ProductCatalog,
    User,
    VideoTask,
)


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


def image_task_payload(
    task: ImageTask,
    user: User | None = None,
    job: GenerationJob | None = None,
) -> dict:
    return {
        "id": task.id,
        "user_id": task.user_id,
        "user_email": user.email if user else None,
        "job_id": task.job_id,
        "job_title": job.title if job else None,
        "scenario": job.scenario if job else None,
        "type_id": task.type_id,
        "title": task.title,
        "size": task.size,
        "status": task.status,
        "progress": task.progress,
        "provider": task.provider,
        "provider_task_id": task.provider_task_id,
        "credit_cost": task.credit_cost,
        "credit_refunded": task.credit_refunded,
        "result_url": task.result_url,
        "error_message": user_visible_task_error(task.error_message),
        "archived": task.archived,
        "created_at": to_utc_iso(task.created_at),
    }


def video_task_payload(
    task: VideoTask,
    user: User | None = None,
    job: GenerationJob | None = None,
) -> dict:
    return {
        "id": task.id,
        "media_type": "video",
        "user_id": task.user_id,
        "user_email": user.email if user else None,
        "job_id": task.job_id,
        "job_title": job.title if job else None,
        "scenario": task.scenario,
        "type_id": task.type_id,
        "title": task.title,
        "size": f"{task.aspect_ratio}/{task.resolution}/{task.duration}s",
        "input_mode": task.input_mode,
        "duration": task.duration,
        "resolution": task.resolution,
        "aspect_ratio": task.aspect_ratio,
        "status": task.status,
        "progress": task.progress,
        "provider": task.provider,
        "provider_task_id": task.provider_task_id,
        "credit_cost": task.credit_cost,
        "credit_refunded": task.credit_refunded,
        "result_url": task.result_url,
        "error_message": user_visible_task_error(task.error_message),
        "archived": task.archived,
        "created_at": to_utc_iso(task.created_at),
    }


def prompt_template_payload(template: PromptTemplate) -> dict:
    return {
        "id": template.id,
        "scenario": template.scenario,
        "purpose": template.purpose,
        "platform": template.platform,
        "type_id": template.type_id,
        "model": template.model,
        "name": template.name,
        "content": template.content,
        "version": template.version,
        "active": template.active,
        "created_at": to_utc_iso(template.created_at),
        "updated_at": to_utc_iso(template.updated_at),
    }


def outfit_model_payload(model: OutfitModel) -> dict:
    return {
        "id": model.id,
        "name": model.name,
        "image_url": model.image_url,
        "object_key": model.object_key,
        "sort_order": model.sort_order,
        "active": model.active,
        "created_at": to_utc_iso(model.created_at),
        "updated_at": to_utc_iso(model.updated_at),
    }


def product_catalog_payload(item: ProductCatalog) -> dict:
    return {
        "id": item.id,
        "scenario": item.scenario,
        "item_id": item.item_id,
        "name": item.name,
        "description": item.description,
        "strategy": item.strategy,
        "default_count": item.default_count,
        "max_count": item.max_count,
        "enabled": item.enabled,
        "sort": item.sort,
        "created_at": to_utc_iso(item.created_at),
        "updated_at": to_utc_iso(item.updated_at),
    }


def audit_log_payload(log: AdminAuditLog, actor: User | None = None) -> dict:
    return {
        "id": log.id,
        "actor_user_id": log.actor_user_id,
        "actor_email": actor.email if actor else None,
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "detail": parse_json_or_none(log.detail_json) or {},
        "created_at": to_utc_iso(log.created_at),
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
