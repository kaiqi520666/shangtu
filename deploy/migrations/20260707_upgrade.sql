BEGIN;

ALTER TABLE generation_jobs
    ADD COLUMN IF NOT EXISTS source_videos_json TEXT,
    ADD COLUMN IF NOT EXISTS source_audios_json TEXT;

ALTER TABLE video_tasks
    ALTER COLUMN input_video_url TYPE TEXT,
    ALTER COLUMN result_url TYPE TEXT;

CREATE TABLE IF NOT EXISTS heygen_avatars (
    id VARCHAR(36) PRIMARY KEY,
    avatar_id VARCHAR(128) NOT NULL UNIQUE,
    group_id VARCHAR(128),
    name VARCHAR(120) NOT NULL,
    avatar_type VARCHAR(32) NOT NULL,
    ownership VARCHAR(20) NOT NULL,
    gender VARCHAR(20),
    default_voice_id VARCHAR(128),
    preferred_orientation VARCHAR(20),
    preview_image_url TEXT,
    preview_video_url TEXT,
    status VARCHAR(20),
    supported_api_engines_json TEXT,
    tags_json TEXT,
    sort_order INTEGER NOT NULL,
    enabled BOOLEAN NOT NULL,
    raw_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_heygen_avatars_enabled_sort
    ON heygen_avatars (enabled, sort_order);
CREATE INDEX IF NOT EXISTS ix_heygen_avatars_type_enabled
    ON heygen_avatars (avatar_type, enabled);

CREATE TABLE IF NOT EXISTS heygen_voices (
    id VARCHAR(36) PRIMARY KEY,
    voice_id VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    gender VARCHAR(20),
    language VARCHAR(50),
    voice_type VARCHAR(20),
    preview_audio_url TEXT,
    support_locale BOOLEAN NOT NULL,
    support_pause BOOLEAN NOT NULL,
    sort_order INTEGER NOT NULL,
    enabled BOOLEAN NOT NULL,
    raw_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_heygen_voices_enabled_sort
    ON heygen_voices (enabled, sort_order);
CREATE INDEX IF NOT EXISTS ix_heygen_voices_language_enabled
    ON heygen_voices (language, enabled);

CREATE TABLE IF NOT EXISTS heygen_translation_languages (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    display_name_zh VARCHAR(120) NOT NULL,
    provider VARCHAR(32) NOT NULL,
    enabled BOOLEAN NOT NULL,
    sort_order INTEGER NOT NULL,
    raw_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_heygen_translation_languages_enabled_sort
    ON heygen_translation_languages (enabled, sort_order);
CREATE INDEX IF NOT EXISTS ix_heygen_translation_languages_provider_name
    ON heygen_translation_languages (provider, name);

CREATE TABLE IF NOT EXISTS user_audio_assets (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    audio_url TEXT NOT NULL,
    object_key VARCHAR(255) NOT NULL,
    duration_seconds INTEGER NOT NULL,
    size INTEGER NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    source VARCHAR(20) NOT NULL,
    enabled BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_user_audio_assets_user_active
    ON user_audio_assets (user_id, enabled, archived_at);
CREATE INDEX IF NOT EXISTS ix_user_audio_assets_user_created
    ON user_audio_assets (user_id, created_at);

CREATE TABLE IF NOT EXISTS user_avatars (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    avatar_type VARCHAR(20) NOT NULL,
    name VARCHAR(120) NOT NULL,
    heygen_avatar_id VARCHAR(128) NOT NULL UNIQUE,
    preview_image_url TEXT,
    preview_video_url TEXT,
    source_image_url TEXT NOT NULL,
    source_object_key VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    enabled BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_user_avatars_user_active
    ON user_avatars (user_id, enabled, archived_at);
CREATE INDEX IF NOT EXISTS ix_user_avatars_user_created
    ON user_avatars (user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_user_avatars_heygen_avatar
    ON user_avatars (heygen_avatar_id);

CREATE TABLE IF NOT EXISTS user_avatar_tasks (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    avatar_type VARCHAR(20) NOT NULL,
    name VARCHAR(120) NOT NULL,
    source_image_url TEXT NOT NULL,
    source_object_key VARCHAR(255) NOT NULL,
    provider VARCHAR(32) NOT NULL,
    provider_task_id VARCHAR(128),
    provider_avatar_id VARCHAR(128),
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    credit_cost INTEGER NOT NULL,
    credit_refunded BOOLEAN NOT NULL,
    result_avatar_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_user_avatar_tasks_user_status
    ON user_avatar_tasks (user_id, status, archived_at);
CREATE INDEX IF NOT EXISTS ix_user_avatar_tasks_user_created
    ON user_avatar_tasks (user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_user_avatar_tasks_provider_task
    ON user_avatar_tasks (provider_task_id);

INSERT INTO system_settings (key, value_json, description, updated_by_user_id, created_at, updated_at)
VALUES
    ('digital_human_credit_costs', '{"standard":7,"premium":16}', '数字人每秒扣费配置', NULL, NOW(), NOW()),
    ('digital_human_precharge_costs', '{"standard":2000,"premium":5000}', '数字人预扣费配置', NULL, NOW(), NOW()),
    ('video_translation_credit_costs', '{"standard":7,"premium":14}', '视频翻译每秒扣费配置', NULL, NOW(), NOW())
ON CONFLICT (key) DO NOTHING;

COMMIT;
