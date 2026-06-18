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
        await conn.execute(
            text(
                """
                ALTER TABLE image_tasks
                ALTER COLUMN prompt TYPE TEXT,
                ADD COLUMN IF NOT EXISTS user_id INTEGER,
                ADD COLUMN IF NOT EXISTS job_id VARCHAR(36),
                ADD COLUMN IF NOT EXISTS replaced_by_task_id VARCHAR(36),
                ADD COLUMN IF NOT EXISTS type_id VARCHAR(50),
                ADD COLUMN IF NOT EXISTS title VARCHAR(100),
                ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS error_message TEXT,
                ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS provider VARCHAR(32) DEFAULT 'toapis',
                ADD COLUMN IF NOT EXISTS provider_task_id VARCHAR(128),
                ADD COLUMN IF NOT EXISTS credit_cost INTEGER NOT NULL DEFAULT 1,
                ADD COLUMN IF NOT EXISTS credit_refunded BOOLEAN NOT NULL DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS prompt_snapshot_json TEXT,
                ADD COLUMN IF NOT EXISTS settings_snapshot_json TEXT,
                ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ,
                DROP COLUMN IF EXISTS edit_instruction,
                DROP COLUMN IF EXISTS system_prompt_snapshot,
                DROP COLUMN IF EXISTS task_prompt_snapshot,
                DROP COLUMN IF EXISTS user_prompt,
                DROP COLUMN IF EXISTS prompt_template_refs_json
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS video_tasks (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    job_id VARCHAR(36),
                    type_id VARCHAR(50),
                    title VARCHAR(100),
                    sort_order INTEGER,
                    prompt TEXT NOT NULL,
                    input_mode VARCHAR(32) NOT NULL,
                    input_images_json TEXT,
                    duration INTEGER NOT NULL,
                    resolution VARCHAR(20) NOT NULL,
                    aspect_ratio VARCHAR(20) NOT NULL,
                    status VARCHAR(20),
                    result_url VARCHAR(500),
                    error_message TEXT,
                    progress INTEGER,
                    provider VARCHAR(32),
                    provider_task_id VARCHAR(128),
                    credit_cost INTEGER NOT NULL DEFAULT 1,
                    credit_refunded BOOLEAN NOT NULL DEFAULT FALSE,
                    prompt_snapshot_json TEXT,
                    settings_snapshot_json TEXT,
                    archived BOOLEAN,
                    archived_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                ALTER TABLE video_tasks
                ADD COLUMN IF NOT EXISTS prompt_snapshot_json TEXT,
                DROP COLUMN IF EXISTS system_prompt_snapshot,
                DROP COLUMN IF EXISTS task_prompt_snapshot,
                DROP COLUMN IF EXISTS user_prompt,
                DROP COLUMN IF EXISTS prompt_template_refs_json
                """
            )
        )
