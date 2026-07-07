from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

from app.core.database import SessionLocal  # noqa: E402
from app.models import GenerationJob, ImageTask, User, VideoTask  # noqa: E402


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return value


def _serialize_model(row: Any) -> dict[str, Any]:
    return {
        column.name: _serialize_value(getattr(row, column.name))
        for column in row.__table__.columns
    }


async def export_records(email: str, output: Path) -> dict[str, Any]:
    async with SessionLocal() as db:
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if user is None:
            raise RuntimeError(f"本地用户不存在：{email}")

        jobs = (
            await db.execute(
                select(GenerationJob)
                .where(GenerationJob.user_id == user.id)
                .order_by(GenerationJob.created_at.asc())
            )
        ).scalars().all()
        image_tasks = (
            await db.execute(
                select(ImageTask)
                .where(ImageTask.user_id == user.id)
                .order_by(ImageTask.created_at.asc())
            )
        ).scalars().all()
        video_tasks = (
            await db.execute(
                select(VideoTask)
                .where(VideoTask.user_id == user.id)
                .order_by(VideoTask.created_at.asc())
            )
        ).scalars().all()

        job_ids = {item.id for item in jobs}
        missing_job_refs = sorted(
            {
                task.job_id
                for task in [*image_tasks, *video_tasks]
                if task.job_id and task.job_id not in job_ids
            }
        )

        payload = {
            "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "source_user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
            },
            "counts": {
                "generation_jobs": len(jobs),
                "image_tasks": len(image_tasks),
                "video_tasks": len(video_tasks),
            },
            "warnings": {
                "missing_job_refs": missing_job_refs,
            },
            "generation_jobs": [_serialize_model(item) for item in jobs],
            "image_tasks": [_serialize_model(item) for item in image_tasks],
            "video_tasks": [_serialize_model(item) for item in video_tasks],
        }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export one user's generation job/image/video records as JSON."
    )
    parser.add_argument("email", help="User email to export")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path. Defaults to deploy/exports/<email>_generation_records.json",
    )
    args = parser.parse_args()

    output = args.output
    if output is None:
        output = (
            PROJECT_DIR
            / "deploy"
            / "exports"
            / f"{_safe_name(args.email)}_generation_records.json"
        )

    payload = await export_records(args.email, output)
    print(f"exported: {output}")
    print(
        "counts:",
        " ".join(f"{key}={value}" for key, value in payload["counts"].items()),
    )
    missing = payload["warnings"]["missing_job_refs"]
    if missing:
        print("warning: missing job refs:", ", ".join(missing))


if __name__ == "__main__":
    asyncio.run(main())
