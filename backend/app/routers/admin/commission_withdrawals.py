from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.commissions import add_wallet_transaction, withdrawal_payload
from app.core.deps import get_current_super_admin, get_db
from app.core.oss import OssConfigError, upload_image_bytes
from app.core.time import utc_now
from app.models import CommissionWithdrawal, User
from app.schemas.response import Response, fail, success

from .utils import audit_log, page_payload

router = APIRouter()


class RejectWithdrawalRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=255)


async def _locked_withdrawal(
    db: AsyncSession, withdrawal_id: str
) -> CommissionWithdrawal | None:
    return (
        await db.execute(
            select(CommissionWithdrawal)
            .where(CommissionWithdrawal.id == withdrawal_id)
            .with_for_update()
        )
    ).scalar_one_or_none()


async def _upload_voucher(file: UploadFile | None, admin_id: int):
    if not file:
        return None
    return await upload_image_bytes(
        user_id=admin_id,
        content=await file.read(),
        content_type=file.content_type or "",
        source="system/withdrawal-vouchers",
    )


@router.get("/commission-withdrawals", response_model=Response)
async def list_withdrawals(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    page, page_size = max(1, page), min(max(1, page_size), 100)
    conditions = []
    if status in {"pending_review", "pending_payment", "paid", "rejected"}:
        conditions.append(CommissionWithdrawal.status == status)
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                User.email.ilike(like),
                CommissionWithdrawal.alipay_name.ilike(like),
                CommissionWithdrawal.alipay_account.ilike(like),
            )
        )
    count_stmt = (
        select(func.count())
        .select_from(CommissionWithdrawal)
        .join(User, User.id == CommissionWithdrawal.user_id)
    )
    data_stmt = (
        select(CommissionWithdrawal, User)
        .join(User, User.id == CommissionWithdrawal.user_id)
        .order_by(CommissionWithdrawal.created_at.desc())
    )
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
        data_stmt = data_stmt.where(condition)
    total = int((await db.scalar(count_stmt)) or 0)
    rows = (
        await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    ).all()
    return success(page_payload([withdrawal_payload(item, user) for item, user in rows], total, page, page_size))


@router.post("/commission-withdrawals/{withdrawal_id}/approve", response_model=Response)
async def approve_withdrawal(
    withdrawal_id: str,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    item = await _locked_withdrawal(db, withdrawal_id)
    if not item:
        return fail("提现申请不存在")
    if item.status != "pending_review":
        return fail("只有待审核申请可以通过审核")
    item.status = "pending_payment"
    item.reviewed_by = current_admin.id
    item.reviewed_at = utc_now()
    db.add(
        audit_log(
            current_admin,
            "approve_commission_withdrawal",
            "commission_withdrawal",
            item.id,
            {"amount_cents": item.amount_cents},
        )
    )
    await db.commit()
    return success(withdrawal_payload(item))


@router.post("/commission-withdrawals/{withdrawal_id}/reject", response_model=Response)
async def reject_withdrawal(
    withdrawal_id: str,
    req: RejectWithdrawalRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    if not req.reason.strip():
        return fail("请填写驳回原因")
    item = await _locked_withdrawal(db, withdrawal_id)
    if not item:
        return fail("提现申请不存在")
    if item.status not in {"pending_review", "pending_payment"}:
        return fail("当前提现申请不能驳回")
    user = (
        await db.execute(select(User).where(User.id == item.user_id).with_for_update())
    ).scalar_one()
    user.commission_frozen_cents -= item.amount_cents
    user.commission_available_cents += item.amount_cents
    item.status = "rejected"
    item.reject_reason = req.reason.strip()
    item.reviewed_by = current_admin.id
    item.reviewed_at = utc_now()
    add_wallet_transaction(
        db,
        user,
        tx_type="withdraw_reject",
        available_delta=item.amount_cents,
        frozen_delta=-item.amount_cents,
        withdrawal_id=item.id,
        note=f"提现驳回：{item.reject_reason}",
    )
    db.add(
        audit_log(
            current_admin,
            "reject_commission_withdrawal",
            "commission_withdrawal",
            item.id,
            {"reason": item.reject_reason},
        )
    )
    await db.commit()
    return success(withdrawal_payload(item))


@router.post("/commission-withdrawals/{withdrawal_id}/pay", response_model=Response)
async def pay_withdrawal(
    withdrawal_id: str,
    payment_reference: str = Form(..., min_length=1, max_length=100),
    voucher: UploadFile | None = File(default=None),
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    if not payment_reference.strip():
        return fail("请填写打款流水号")
    item = await _locked_withdrawal(db, withdrawal_id)
    if not item:
        return fail("提现申请不存在")
    if item.status != "pending_payment":
        return fail("只有待打款申请可以确认打款")
    try:
        uploaded = await _upload_voucher(voucher, current_admin.id)
    except (OssConfigError, ValueError) as exc:
        return fail(str(exc))
    user = (
        await db.execute(select(User).where(User.id == item.user_id).with_for_update())
    ).scalar_one()
    user.commission_frozen_cents -= item.amount_cents
    user.commission_withdrawn_cents += item.amount_cents
    item.status = "paid"
    item.payment_reference = payment_reference.strip()
    item.voucher_url = uploaded.url if uploaded else None
    item.voucher_object_key = uploaded.object_key if uploaded else None
    item.reviewed_by = current_admin.id
    item.paid_at = utc_now()
    add_wallet_transaction(
        db,
        user,
        tx_type="withdraw_paid",
        available_delta=0,
        frozen_delta=-item.amount_cents,
        withdrawal_id=item.id,
        note=f"提现已打款 · {item.payment_reference}",
    )
    db.add(
        audit_log(
            current_admin,
            "pay_commission_withdrawal",
            "commission_withdrawal",
            item.id,
            {"payment_reference": item.payment_reference},
        )
    )
    await db.commit()
    return success(withdrawal_payload(item))
