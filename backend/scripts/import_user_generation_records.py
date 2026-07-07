from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

from app.core.database import SessionLocal  # noqa: E402
from app.models import GenerationJob, ImageTask, User, VideoTask  # noqa: E402


def _parse_datetime(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return value


def _coerce_row(model: type, row: dict[str, Any], *, target_user_id: int) -> dict[str, Any]:
    column_names = {column.name for column in model.__table__.columns}
    values = {
        key: _parse_datetime(value)
        for key, value in row.items()
        if key in column_names
    }
    values["user_id"] = target_user_id
    return values


async def _upsert_rows(db, model: type, rows: list[dict[str, Any]], *, target_user_id: int) -> dict[str, int]:
    inserted = 0
    updated = 0
    skipped = 0
    for raw_row in rows:
        values = _coerce_row(model, raw_row, target_user_id=target_user_id)
        row_id = values.get("id")
        if not row_id:
            skipped += 1
            continue

        current = await db.get(model, row_id)
        if current is None:
            db.add(model(**values))
            inserted += 1
            continue

        current_user_id = getattr(current, "user_id", None)
        if current_user_id != target_user_id:
            raise RuntimeError(
                f"{model.__tablename__}.{row_id} 已存在，但属于 user_id={current_user_id}，"
                f"目标用户 user_id={target_user_id}，为避免覆盖他人数据已中止"
            )

        for key, value in values.items():
            setattr(current, key, value)
        updated += 1

    return {"inserted": inserted, "updated": updated, "skipped": skipped}


async def import_records(input_path: Path, *, email: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    target_email = email or payload.get("source_user", {}).get("email")
    if not target_email:
        raise RuntimeError("导入文件缺少 source_user.email，请用 --email 指定目标用户邮箱")

    async with SessionLocal() as db:
        target_user = (
            await db.execute(select(User).where(User.email == target_email))
        ).scalar_one_or_none()
        if target_user is None:
            raise RuntimeError(f"云端用户不存在：{target_email}")

        result = {
            "target_user": {
                "id": target_user.id,
                "email": target_user.email,
                "username": target_user.username,
            },
            "generation_jobs": await _upsert_rows(
                db,
                GenerationJob,
                payload.get("generation_jobs", []),
                target_user_id=target_user.id,
            ),
            "image_tasks": await _upsert_rows(
                db,
                ImageTask,
                payload.get("image_tasks", []),
                target_user_id=target_user.id,
            ),
            "video_tasks": await _upsert_rows(
                db,
                VideoTask,
                payload.get("video_tasks", []),
                target_user_id=target_user.id,
            ),
        }

        if dry_run:
            await db.rollback()
        else:
            await db.commit()
        return result


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import one user's exported generation job/image/video records."
    )
    parser.add_argument("input", type=Path, help="Export JSON path")
    parser.add_argument("--email", default=None, help="Target cloud user email")
    parser.add_argument("--dry-run", action="store_true", help="Validate without committing")
    args = parser.parse_args()

    result = await import_records(args.input, email=args.email, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.dry_run:
        print("DRY RUN: rolled back")


if __name__ == "__main__":
    asyncio.run(main())
