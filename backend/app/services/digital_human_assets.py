from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HeygenAvatar, HeygenVoice, UserAvatar


class ResolvedAvatar(BaseModel):
    avatar_id: str
    name: str
    preview_image_url: str = ""
    preview_video_url: str = ""
    source: str = "system"
    asset_id: str = ""
    avatar_type: str = "studio_avatar"


async def resolve_avatar(
    db: AsyncSession,
    *,
    avatar_id: str,
    user_id: int,
) -> ResolvedAvatar | None:
    result = await db.execute(
        select(UserAvatar).where(
            UserAvatar.user_id == user_id,
            UserAvatar.heygen_avatar_id == avatar_id,
            UserAvatar.enabled == True,  # noqa: E712
            UserAvatar.status == "active",
            UserAvatar.archived_at.is_(None),
        )
    )
    user_avatar = result.scalar_one_or_none()
    if user_avatar:
        return ResolvedAvatar(
            avatar_id=user_avatar.heygen_avatar_id,
            name=user_avatar.name,
            preview_image_url=user_avatar.preview_image_url
            or user_avatar.source_image_url
            or "",
            preview_video_url=user_avatar.preview_video_url or "",
            source="photo",
            asset_id=user_avatar.id,
            avatar_type=user_avatar.avatar_type,
        )
    result = await db.execute(
        select(HeygenAvatar).where(
            HeygenAvatar.avatar_id == avatar_id,
            HeygenAvatar.enabled == True,  # noqa: E712
        )
    )
    avatar = result.scalar_one_or_none()
    if not avatar:
        return None
    return ResolvedAvatar(
        avatar_id=avatar.avatar_id,
        name=avatar.name,
        preview_image_url=avatar.preview_image_url or "",
        preview_video_url=avatar.preview_video_url or "",
        source="system",
        asset_id=avatar.id,
        avatar_type=avatar.avatar_type,
    )


async def get_enabled_voice(
    db: AsyncSession,
    voice_id: str,
) -> HeygenVoice | None:
    result = await db.execute(
        select(HeygenVoice).where(
            HeygenVoice.voice_id == voice_id,
            HeygenVoice.enabled == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()
