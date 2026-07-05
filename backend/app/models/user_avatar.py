from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utc_now


class UserAvatar(Base):
    __tablename__ = "user_avatars"
    __table_args__ = (
        Index("ix_user_avatars_user_active", "user_id", "enabled", "archived_at"),
        Index("ix_user_avatars_user_created", "user_id", "created_at"),
        Index("ix_user_avatars_heygen_avatar", "heygen_avatar_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    avatar_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    heygen_avatar_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    preview_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_image_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_object_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
