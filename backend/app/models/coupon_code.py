from datetime import datetime
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class CouponCode(Base):
    __tablename__ = "coupon_codes"
    __table_args__ = (
        CheckConstraint("credits >= 1 AND credits <= 10000000", name="ck_coupon_codes_credits"),
        CheckConstraint(
            "usage_limit IS NULL OR (usage_limit > 0 AND usage_limit <= 1000000)",
            name="ck_coupon_codes_usage_limit",
        ),
        CheckConstraint("used_count >= 0", name="ck_coupon_codes_used_count"),
        CheckConstraint(
            "usage_limit IS NULL OR used_count <= usage_limit",
            name="ck_coupon_codes_usage_count",
        ),
        Index("ix_coupon_codes_code", "code", unique=True),
        Index("ix_coupon_codes_status", "deleted_at", "enabled"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
