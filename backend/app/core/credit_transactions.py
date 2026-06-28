from app.core.time import to_utc_iso
from app.models import CreditTransaction, User


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
