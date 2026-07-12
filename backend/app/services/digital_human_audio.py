from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import to_utc_iso, utc_now
from app.models import UserAudioAsset


def audio_asset_payload(asset: UserAudioAsset) -> dict:
    return {
        "id": asset.id,
        "name": asset.name,
        "audio_url": asset.audio_url,
        "object_key": asset.object_key,
        "duration_seconds": int(asset.duration_seconds or 0),
        "size": int(asset.size or 0),
        "content_type": asset.content_type,
        "source": asset.source,
        "enabled": bool(asset.enabled),
        "created_at": to_utc_iso(asset.created_at),
        "updated_at": to_utc_iso(asset.updated_at),
    }


async def get_available_audio_asset(
    db: AsyncSession,
    *,
    audio_asset_id: str,
    user_id: int,
) -> UserAudioAsset | None:
    result = await db.execute(
        select(UserAudioAsset).where(
            UserAudioAsset.id == audio_asset_id,
            UserAudioAsset.user_id == user_id,
            UserAudioAsset.enabled == True,  # noqa: E712
            UserAudioAsset.archived_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def archive_audio_asset(
    db: AsyncSession,
    *,
    audio_asset_id: str,
    user_id: int,
) -> str | None:
    asset = await get_available_audio_asset(
        db,
        audio_asset_id=audio_asset_id,
        user_id=user_id,
    )
    if not asset:
        return "音频不存在"

    asset.enabled = False
    asset.archived_at = utc_now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return "删除失败，请稍后重试"
    return None
