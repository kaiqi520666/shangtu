from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"
    __table_args__ = (
        UniqueConstraint(
            "coupon_code_id", "user_id", name="uq_coupon_redemptions_coupon_user"
        ),
        Index("ix_coupon_redemptions_user_created", "user_id", "created_at"),
        Index("ix_coupon_redemptions_coupon_created", "coupon_code_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    coupon_code_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("coupon_codes.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    code_snapshot: Mapped[str] = mapped_column(String(32), nullable=False)
    credits_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_transaction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("credit_transactions.id"), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
