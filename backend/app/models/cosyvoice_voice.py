from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class CosyVoiceVoice(Base):
    __tablename__ = "cosyvoice_voices"
    __table_args__ = (
        UniqueConstraint("model_id", "voice_id", name="uq_cosyvoice_voices_model_voice"),
        Index("ix_cosyvoice_voices_model_enabled_sort", "model_id", "enabled", "sort_order"),
        Index("ix_cosyvoice_voices_category_enabled", "category", "enabled"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    voice_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    trait: Mapped[str] = mapped_column(String(120), nullable=False)
    age_range: Mapped[str] = mapped_column(String(40), nullable=False)
    languages: Mapped[str] = mapped_column(Text, nullable=False)
    supports_ssml: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_instruct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_timestamp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    regions: Mapped[str] = mapped_column(Text, nullable=False)
    preview_audio_url: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
