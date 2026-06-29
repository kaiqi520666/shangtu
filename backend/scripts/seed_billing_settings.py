from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.system_settings import seed_default_billing_settings  # noqa: E402
import app.models  # noqa: E402,F401


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        results = await seed_default_billing_settings(db, overwrite=True)
        await db.commit()

    print("billing settings seeded:", " ".join(f"{key}={value}" for key, value in results.items()))


if __name__ == "__main__":
    asyncio.run(main())
