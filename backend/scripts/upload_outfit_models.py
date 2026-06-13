from __future__ import annotations

import asyncio
import mimetypes
import sys
from pathlib import Path

import oss2
from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR.parent
MODEL_DIR = PROJECT_DIR / "frontend" / "public" / "model"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.oss import build_public_url, get_oss_config  # noqa: E402
from app.core.time import utc_now  # noqa: E402
from app.models import OutfitModel  # noqa: E402
import app.models  # noqa: E402,F401

ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
OSS_PREFIX = "system/outfit-models"


def _iter_model_files() -> list[Path]:
    if not MODEL_DIR.exists():
        raise RuntimeError(f"模特图片目录不存在: {MODEL_DIR}")

    files = [
        item
        for item in MODEL_DIR.iterdir()
        if item.is_file() and item.suffix.lower() in ALLOWED_SUFFIXES
    ]
    return sorted(files, key=lambda item: item.name.lower())


def _upload_file(path: Path) -> tuple[str, str]:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    config = get_oss_config()
    object_key = f"{OSS_PREFIX}/{path.name}"
    auth = oss2.Auth(config["access_key_id"], config["access_key_secret"])
    bucket = oss2.Bucket(auth, config["endpoint"], config["bucket_name"])
    bucket.put_object_from_file(
        object_key,
        str(path),
        headers={"Content-Type": content_type},
    )
    return object_key, build_public_url(object_key, config)


async def upsert_models() -> tuple[int, int, int]:
    files = _iter_model_files()
    if not files:
        raise RuntimeError(f"模特图片目录为空: {MODEL_DIR}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    inserted = 0
    updated = 0
    unchanged = 0
    async with SessionLocal() as db:
        for index, path in enumerate(files, start=1):
            object_key, image_url = await asyncio.to_thread(_upload_file, path)
            result = await db.execute(
                select(OutfitModel).where(OutfitModel.object_key == object_key)
            )
            model = result.scalar_one_or_none()
            name = f"模特 {index:02d}"
            if model is None:
                db.add(
                    OutfitModel(
                        name=name,
                        image_url=image_url,
                        object_key=object_key,
                        sort_order=index,
                        active=True,
                    )
                )
                inserted += 1
                continue

            changed = False
            updates = {
                "name": name,
                "image_url": image_url,
                "sort_order": index,
                "active": True,
            }
            for field_name, value in updates.items():
                if getattr(model, field_name) != value:
                    setattr(model, field_name, value)
                    changed = True

            if changed:
                model.updated_at = utc_now()
                updated += 1
            else:
                unchanged += 1

        await db.commit()

    return inserted, updated, unchanged


async def main() -> None:
    inserted, updated, unchanged = await upsert_models()
    print(
        f"outfit models uploaded: inserted={inserted}, "
        f"updated={updated}, unchanged={unchanged}"
    )


if __name__ == "__main__":
    asyncio.run(main())
