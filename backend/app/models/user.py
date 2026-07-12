from datetime import datetime

from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "consumption_multiplier >= 0.01 AND consumption_multiplier <= 9.99",
            name="ck_users_consumption_multiplier",
        ),
        CheckConstraint(
            "distribution_level IS NULL OR distribution_level IN (1, 2, 3)",
            name="ck_users_distribution_level",
        ),
        CheckConstraint(
            "commission_rate IS NULL OR (commission_rate >= 0 AND commission_rate <= 100)",
            name="ck_users_commission_rate",
        ),
        CheckConstraint(
            "commission_available_cents >= 0 AND commission_frozen_cents >= 0 AND commission_withdrawn_cents >= 0",
            name="ck_users_commission_balances",
        ),
        Index("ix_users_distribution_parent", "distribution_parent_id"),
        Index("ix_users_invite_code", "invite_code", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=0)
    consumption_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=Decimal("1.00"), nullable=False
    )
    distribution_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distribution_parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    commission_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    invite_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    distribution_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    commission_available_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    commission_frozen_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    commission_withdrawn_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
