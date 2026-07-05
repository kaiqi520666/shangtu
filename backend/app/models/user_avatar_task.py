from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class UserAvatarTask(Base):
    __tablename__ = "user_avatar_tasks"
    __table_args__ = (
        Index("ix_user_avatar_tasks_user_status", "user_id", "status", "archived_at"),
        Index("ix_user_avatar_tasks_user_created", "user_id", "created_at"),
        Index("ix_user_avatar_tasks_provider_task", "provider_task_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    avatar_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_image_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_object_key: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), default="heygen", nullable=False)
    provider_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider_avatar_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    credit_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credit_refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    result_avatar_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
