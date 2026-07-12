from app.core.time import to_utc_iso
from app.models import CommissionTransaction, CommissionWithdrawal, User


def commission_transaction_payload(tx: CommissionTransaction) -> dict:
    return {
        "id": tx.id,
        "type": tx.type,
        "available_delta_cents": tx.available_delta_cents,
        "frozen_delta_cents": tx.frozen_delta_cents,
        "available_after_cents": tx.available_after_cents,
        "frozen_after_cents": tx.frozen_after_cents,
        "source_amount_cents": tx.source_amount_cents,
        "commission_rate": float(tx.commission_rate) if tx.commission_rate is not None else None,
        "note": tx.note,
        "created_at": to_utc_iso(tx.created_at),
    }


def withdrawal_payload(item: CommissionWithdrawal, user: User | None = None) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "user_email": user.email if user else None,
        "amount_cents": item.amount_cents,
        "alipay_name": item.alipay_name,
        "alipay_account": item.alipay_account,
        "status": item.status,
        "reject_reason": item.reject_reason,
        "payment_reference": item.payment_reference,
        "voucher_url": item.voucher_url,
        "reviewed_at": to_utc_iso(item.reviewed_at),
        "paid_at": to_utc_iso(item.paid_at),
        "created_at": to_utc_iso(item.created_at),
    }


def add_wallet_transaction(
    db,
    user: User,
    *,
    tx_type: str,
    available_delta: int,
    frozen_delta: int,
    withdrawal_id: str,
    note: str,
) -> None:
    db.add(
        CommissionTransaction(
            user_id=user.id,
            withdrawal_id=withdrawal_id,
            type=tx_type,
            available_delta_cents=available_delta,
            frozen_delta_cents=frozen_delta,
            available_after_cents=user.commission_available_cents,
            frozen_after_cents=user.commission_frozen_cents,
            note=note,
        )
    )
