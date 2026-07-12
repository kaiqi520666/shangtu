import secrets
from decimal import Decimal, ROUND_FLOOR

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import dump_json, parse_json_or_none
from app.models import CommissionTransaction, CreditOrder, User


def generate_invite_code() -> str:
    return secrets.token_urlsafe(9)


async def update_root_distribution(
    db: AsyncSession,
    user: User,
    *,
    enabled: bool | None,
    rate: Decimal | None,
) -> bool:
    if user.distribution_level not in {None, 1}:
        raise ValueError("只有一级分销用户可以由管理员启用或停止")
    changed = False
    if enabled is not None and enabled != user.distribution_enabled:
        if user.distribution_level is None:
            user.distribution_level = 1
            user.commission_rate = rate if rate is not None else Decimal("10.00")
            user.invite_code = generate_invite_code()
        child_ids = list(
            (await db.execute(select(User.id).where(User.distribution_parent_id == user.id))).scalars()
        )
        grandchild_ids = list(
            (await db.execute(select(User.id).where(User.distribution_parent_id.in_(child_ids)))).scalars()
        ) if child_ids else []
        await db.execute(
            update(User)
            .where(User.id.in_([user.id, *child_ids, *grandchild_ids]))
            .values(distribution_enabled=enabled)
        )
        user.distribution_enabled = enabled
        if not enabled:
            await db.execute(
                update(CreditOrder)
                .where(
                    CreditOrder.distribution_root_user_id == user.id,
                    CreditOrder.status == "pending",
                )
                .values(distribution_snapshot_json=None)
            )
        changed = True
    if rate is not None and rate != user.commission_rate:
        if user.distribution_level != 1:
            raise ValueError("管理员只能设置一级分销比例")
        max_child_rate = await db.scalar(
            select(func.max(User.commission_rate)).where(User.distribution_parent_id == user.id)
        )
        if max_child_rate is not None and rate < max_child_rate:
            raise ValueError("一级比例不能低于现有二级比例")
        user.commission_rate = rate
        changed = True
    return changed


async def build_distribution_snapshot(
    db: AsyncSession, user_id: int
) -> tuple[str | None, int | None]:
    chain = []
    user = await db.get(User, user_id)
    while user and user.distribution_level and len(chain) < 3:
        chain.append(user)
        if not user.distribution_parent_id:
            break
        user = await db.get(User, user.distribution_parent_id)
    if not chain or chain[-1].distribution_level != 1:
        return None, None
    if any(not item.distribution_enabled for item in chain):
        return None, None

    lower_rate = Decimal("0")
    allocations = []
    for item in chain:
        rate = Decimal(str(item.commission_rate or 0))
        differential = rate - lower_rate
        if differential > 0:
            allocations.append({"user_id": item.id, "rate": f"{differential:.2f}"})
        lower_rate = rate
    return dump_json({"source_user_id": user_id, "allocations": allocations}), chain[-1].id


async def apply_order_commissions(db: AsyncSession, order: CreditOrder) -> None:
    snapshot = parse_json_or_none(order.distribution_snapshot_json)
    allocations = snapshot.get("allocations", []) if isinstance(snapshot, dict) else []
    if not allocations:
        return
    user_ids = sorted({int(item["user_id"]) for item in allocations})
    users = (
        await db.execute(select(User).where(User.id.in_(user_ids)).order_by(User.id).with_for_update())
    ).scalars().all()
    users_by_id = {user.id: user for user in users}
    for item in allocations:
        beneficiary = users_by_id[int(item["user_id"])]
        rate = Decimal(str(item["rate"]))
        amount = int(
            (Decimal(order.amount_cents) * rate / Decimal("100")).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        if amount < 1:
            continue
        beneficiary.commission_available_cents += amount
        db.add(
            CommissionTransaction(
                user_id=beneficiary.id,
                source_user_id=order.user_id,
                order_id=order.id,
                type="earning",
                available_delta_cents=amount,
                frozen_delta_cents=0,
                available_after_cents=beneficiary.commission_available_cents,
                frozen_after_cents=beneficiary.commission_frozen_cents,
                source_amount_cents=order.amount_cents,
                commission_rate=rate,
                note=f"充值订单 {order.out_trade_no} 分佣",
            )
        )
