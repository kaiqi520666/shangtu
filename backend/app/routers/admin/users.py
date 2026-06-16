from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.time import utc_now
from app.models import CreditTransaction, User
from app.schemas.response import Response, fail, success

from .schemas import AdjustCreditsRequest, UpdateUserRequest
from .utils import audit_log, page_payload, super_admin_count, user_payload

router = APIRouter()


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
    return success(page_payload([user_payload(user) for user in users], total, page, page_size))


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
    if would_remove_active_super_admin and await super_admin_count(db) <= 1:
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
        return success(user_payload(target))

    db.add(
        audit_log(
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
    return success(user_payload(target))


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
        audit_log(
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
    return success(user_payload(target))
