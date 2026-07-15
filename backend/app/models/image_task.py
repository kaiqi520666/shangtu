from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class ImageTask(Base):
    __tablename__ = "image_tasks"
    __table_args__ = (
        Index("ix_image_tasks_user_active_created", "user_id", "archived", "created_at"),
        Index(
            "ix_image_tasks_job_active_current",
            "job_id",
            "user_id",
            "archived",
            "replaced_by_task_id",
        ),
        Index("ix_image_tasks_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    replaced_by_task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    type_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    size: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    result_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str] = mapped_column(String(32), default="toapis")
    provider_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    credit_cost: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    credit_refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prompt_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    settings_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
