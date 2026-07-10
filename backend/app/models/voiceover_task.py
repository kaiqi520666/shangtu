from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class VoiceoverTask(Base):
    __tablename__ = "voiceover_tasks"
    __table_args__ = (
        Index("ix_voiceover_tasks_job_active_created", "job_id", "archived", "created_at"),
        Index("ix_voiceover_tasks_user_status_created", "user_id", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    voice_id: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    pitch: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    volume: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    instruction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    usage_characters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    credit_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    result_asset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    settings_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
