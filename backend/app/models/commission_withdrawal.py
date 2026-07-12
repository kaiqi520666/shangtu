from datetime import datetime
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class CommissionWithdrawal(Base):
    __tablename__ = "commission_withdrawals"
    __table_args__ = (
        CheckConstraint("amount_cents >= 10000", name="ck_commission_withdrawals_amount"),
        CheckConstraint(
            "status IN ('pending_review', 'pending_payment', 'paid', 'rejected')",
            name="ck_commission_withdrawals_status",
        ),
        Index("ix_commission_withdrawals_user_created", "user_id", "created_at"),
        Index("ix_commission_withdrawals_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    alipay_name: Mapped[str] = mapped_column(String(100), nullable=False)
    alipay_account: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending_review", nullable=False)
    reject_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    voucher_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    voucher_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
