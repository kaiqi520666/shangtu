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
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS system_settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    description VARCHAR(255),
                    updated_by_user_id INTEGER,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
        )
