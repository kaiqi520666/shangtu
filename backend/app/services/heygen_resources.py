from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import dump_json
from app.core.providers.heygen_provider import (
    iter_public_studio_avatar_looks,
    iter_public_voices,
)
from app.models import HeygenAvatar, HeygenVoice


def _clean_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _avatar_values(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "group_id": _clean_text(item.get("group_id")),
        "name": _clean_text(item.get("name")) or "未命名数字人",
        "avatar_type": _clean_text(item.get("avatar_type")) or "studio_avatar",
        "ownership": "public",
        "gender": _clean_text(item.get("gender")),
        "default_voice_id": _clean_text(item.get("default_voice_id")),
        "preferred_orientation": _clean_text(item.get("preferred_orientation")),
        "preview_image_url": _clean_text(item.get("preview_image_url")),
        "preview_video_url": _clean_text(item.get("preview_video_url")),
        "status": _clean_text(item.get("status")),
        "supported_api_engines_json": dump_json(item.get("supported_api_engines") or []),
        "tags_json": dump_json(item.get("tags") or []),
        "raw_json": dump_json(item),
    }


def _voice_values(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": _clean_text(item.get("name")) or "未命名声音",
        "gender": _clean_text(item.get("gender")),
        "language": _clean_text(item.get("language")),
        "voice_type": _clean_text(item.get("type")),
        "preview_audio_url": _clean_text(item.get("preview_audio_url")),
        "support_locale": bool(item.get("support_locale")),
        "support_pause": bool(item.get("support_pause")),
        "raw_json": dump_json(item),
    }


async def sync_heygen_resources(db: AsyncSession) -> dict[str, int]:
    avatar_result = await db.execute(select(HeygenAvatar))
    voice_result = await db.execute(select(HeygenVoice))

    existing_avatars = {item.avatar_id: item for item in avatar_result.scalars().all()}
    existing_voices = {item.voice_id: item for item in voice_result.scalars().all()}

    stats = {
        "avatar_total": 0,
        "avatar_created": 0,
        "avatar_updated": 0,
        "voice_total": 0,
        "voice_created": 0,
        "voice_updated": 0,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        async for item in iter_public_studio_avatar_looks(client):
            avatar_id = _clean_text(item.get("id"))
            if not avatar_id:
                continue
            stats["avatar_total"] += 1
            values = _avatar_values(item)
            current = existing_avatars.get(avatar_id)
            if current is None:
                db.add(HeygenAvatar(avatar_id=avatar_id, **values))
                stats["avatar_created"] += 1
            else:
                for key, value in values.items():
                    setattr(current, key, value)
                stats["avatar_updated"] += 1

        async for item in iter_public_voices(client):
            voice_id = _clean_text(item.get("voice_id"))
            if not voice_id:
                continue
            stats["voice_total"] += 1
            values = _voice_values(item)
            current = existing_voices.get(voice_id)
            if current is None:
                db.add(HeygenVoice(voice_id=voice_id, **values))
                stats["voice_created"] += 1
            else:
                for key, value in values.items():
                    setattr(current, key, value)
                stats["voice_updated"] += 1

    return stats
