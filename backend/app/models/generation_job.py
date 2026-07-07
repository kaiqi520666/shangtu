from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    scenario: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_images_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_videos_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_audios_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    structure_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
