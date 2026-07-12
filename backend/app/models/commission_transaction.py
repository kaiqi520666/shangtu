from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class CommissionTransaction(Base):
    __tablename__ = "commission_transactions"
    __table_args__ = (
        Index("ix_commission_transactions_user_created", "user_id", "created_at"),
        Index(
            "uq_commission_transactions_order_user_type",
            "order_id",
            "user_id",
            "type",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    source_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    order_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("credit_orders.id"), nullable=True
    )
    withdrawal_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("commission_withdrawals.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(24), nullable=False)
    available_delta_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    frozen_delta_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_after_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    frozen_after_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    source_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commission_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
