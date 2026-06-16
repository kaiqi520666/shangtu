from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def ensure_runtime_schema(engine: AsyncEngine) -> None:
    """Small startup migrations for legacy MVP databases without Alembic."""
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS role VARCHAR(32) NOT NULL DEFAULT 'user',
                ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active',
                ADD COLUMN IF NOT EXISTS disabled_at TIMESTAMPTZ
                """
            )
        )
