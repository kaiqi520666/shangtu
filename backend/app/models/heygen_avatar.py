from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class HeygenAvatar(Base):
    __tablename__ = "heygen_avatars"
    __table_args__ = (
        Index("ix_heygen_avatars_enabled_sort", "enabled", "sort_order"),
        Index("ix_heygen_avatars_type_enabled", "avatar_type", "enabled"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    avatar_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    group_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar_type: Mapped[str] = mapped_column(String(32), nullable=False)
    ownership: Mapped[str] = mapped_column(String(20), default="public", nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    default_voice_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    preferred_orientation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preview_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    supported_api_engines_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
