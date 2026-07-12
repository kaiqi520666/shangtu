import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.pagination import page_payload
from app.core.time import to_utc_iso, utc_now
from app.models import CouponCode, User
from app.schemas.response import Response, fail, success

from .schemas import CreateCouponCodeRequest, UpdateCouponCodeRequest
from .utils import audit_log

router = APIRouter()


def coupon_payload(coupon: CouponCode, creator: User | None = None) -> dict:
    return {
        "id": coupon.id,
        "code": coupon.code,
        "credits": coupon.credits,
        "usage_limit": coupon.usage_limit,
        "used_count": coupon.used_count,
        "enabled": coupon.enabled,
        "deleted_at": to_utc_iso(coupon.deleted_at),
        "created_by_user_id": coupon.created_by_user_id,
        "created_by_email": creator.email if creator else None,
        "created_at": to_utc_iso(coupon.created_at),
        "updated_at": to_utc_iso(coupon.updated_at),
    }


@router.get("/coupon-codes", response_model=Response)
async def list_coupon_codes(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = []
    if keyword:
        conditions.append(CouponCode.code.ilike(f"%{keyword.strip()}%"))
    if status == "deleted":
        conditions.append(CouponCode.deleted_at.is_not(None))
    else:
        conditions.append(CouponCode.deleted_at.is_(None))
        if status == "enabled":
            conditions.append(CouponCode.enabled.is_(True))
        elif status == "disabled":
            conditions.append(CouponCode.enabled.is_(False))

    total = int(
        (
            await db.execute(
                select(func.count()).select_from(CouponCode).where(*conditions)
            )
        ).scalar_one()
        or 0
    )
    result = await db.execute(
        select(CouponCode, User)
        .join(User, User.id == CouponCode.created_by_user_id)
        .where(*conditions)
        .order_by(CouponCode.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [coupon_payload(coupon, creator) for coupon, creator in result.all()]
    return success(page_payload(items, total, page, page_size))


@router.post("/coupon-codes", response_model=Response)
async def create_coupon_code(
    req: CreateCouponCodeRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    if await db.scalar(select(CouponCode.id).where(CouponCode.code == req.code)):
        return fail("优惠码已存在")
    coupon = CouponCode(
        id=str(uuid.uuid4()),
        code=req.code,
        credits=req.credits,
        usage_limit=req.usage_limit,
        enabled=req.enabled,
        created_by_user_id=current_admin.id,
    )
    db.add(coupon)
    db.add(
        audit_log(
            current_admin,
            "create_coupon_code",
            "coupon_code",
            coupon.id,
            {"code": coupon.code, "credits": coupon.credits, "usage_limit": coupon.usage_limit},
        )
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return fail("优惠码已存在")
    await db.refresh(coupon)
    return success(coupon_payload(coupon, current_admin))


@router.patch("/coupon-codes/{coupon_id}", response_model=Response)
async def update_coupon_code(
    coupon_id: str,
    req: UpdateCouponCodeRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    coupon = (
        await db.execute(
            select(CouponCode)
            .where(CouponCode.id == coupon_id, CouponCode.deleted_at.is_(None))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if not coupon:
        return fail("优惠码不存在或已删除")
    next_limit = req.usage_limit if "usage_limit" in req.model_fields_set else coupon.usage_limit
    if next_limit is not None and next_limit < coupon.used_count:
        return fail("使用上限不能低于已使用次数")
    old = {"credits": coupon.credits, "usage_limit": coupon.usage_limit, "enabled": coupon.enabled}
    if req.credits is not None:
        coupon.credits = req.credits
    if "usage_limit" in req.model_fields_set:
        coupon.usage_limit = req.usage_limit
    if req.enabled is not None:
        coupon.enabled = req.enabled
    new = {"credits": coupon.credits, "usage_limit": coupon.usage_limit, "enabled": coupon.enabled}
    if old == new:
        return success(coupon_payload(coupon))
    action = "toggle_coupon_code" if req.model_fields_set == {"enabled"} else "update_coupon_code"
    db.add(audit_log(current_admin, action, "coupon_code", coupon.id, {"old": old, "new": new}))
    await db.commit()
    await db.refresh(coupon)
    return success(coupon_payload(coupon))


@router.delete("/coupon-codes/{coupon_id}", response_model=Response)
async def delete_coupon_code(
    coupon_id: str,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    coupon = (
        await db.execute(
            select(CouponCode)
            .where(CouponCode.id == coupon_id, CouponCode.deleted_at.is_(None))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if not coupon:
        return fail("优惠码不存在或已删除")
    coupon.enabled = False
    coupon.deleted_at = utc_now()
    db.add(
        audit_log(
            current_admin,
            "delete_coupon_code",
            "coupon_code",
            coupon.id,
            {"code": coupon.code, "used_count": coupon.used_count},
        )
    )
    await db.commit()
    return success(message="优惠码已删除")
