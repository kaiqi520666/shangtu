from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class HeygenVoice(Base):
    __tablename__ = "heygen_voices"
    __table_args__ = (
        Index("ix_heygen_voices_enabled_sort", "enabled", "sort_order"),
        Index("ix_heygen_voices_language_enabled", "language", "enabled"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    voice_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    voice_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preview_audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_locale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    support_pause: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
