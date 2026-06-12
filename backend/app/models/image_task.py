from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class ImageTask(Base):
    __tablename__ = "image_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
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
    credit_refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edit_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
