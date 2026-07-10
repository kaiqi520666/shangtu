from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
from sqlalchemy import delete, select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.cosyvoice_catalog import (  # noqa: E402
    COSYVOICE_V3_FLASH,
    COSYVOICE_VOICE_LIST_URL,
    parse_cosyvoice_v3_flash_voices,
    validate_cosyvoice_v3_flash_voices,
)
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.time import utc_now  # noqa: E402
from app.models import CosyVoiceVoice  # noqa: E402
import app.models  # noqa: E402,F401


async def fetch_voice_rows() -> list[dict]:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(
            COSYVOICE_VOICE_LIST_URL,
            headers={"User-Agent": "ShangTu-CosyVoice-Catalog-Sync/1.0"},
        )
        response.raise_for_status()
    rows = parse_cosyvoice_v3_flash_voices(response.text)
    validate_cosyvoice_v3_flash_voices(rows)
    return rows


async def sync_voices() -> tuple[int, int, int, int]:
    rows = await fetch_voice_rows()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    inserted = 0
    updated = 0
    unchanged = 0
    voice_ids = {row["voice_id"] for row in rows}
    async with SessionLocal() as db:
        result = await db.execute(
            select(CosyVoiceVoice).where(CosyVoiceVoice.model_id == COSYVOICE_V3_FLASH)
        )
        existing = {voice.voice_id: voice for voice in result.scalars().all()}
        for row in rows:
            voice = existing.get(row["voice_id"])
            if voice is None:
                db.add(CosyVoiceVoice(**row))
                inserted += 1
                continue
            changed = False
            for field_name, value in row.items():
                if getattr(voice, field_name) != value:
                    setattr(voice, field_name, value)
                    changed = True
            if changed:
                voice.updated_at = utc_now()
                updated += 1
            else:
                unchanged += 1

        stale_ids = set(existing) - voice_ids
        if stale_ids:
            await db.execute(
                delete(CosyVoiceVoice).where(
                    CosyVoiceVoice.model_id == COSYVOICE_V3_FLASH,
                    CosyVoiceVoice.voice_id.in_(stale_ids),
                )
            )
        await db.commit()
    return inserted, updated, unchanged, len(stale_ids)


async def main() -> None:
    inserted, updated, unchanged, deleted = await sync_voices()
    print(
        "CosyVoice voices synced:",
        f"inserted={inserted}",
        f"updated={updated}",
        f"unchanged={unchanged}",
        f"deleted={deleted}",
    )


if __name__ == "__main__":
    asyncio.run(main())
