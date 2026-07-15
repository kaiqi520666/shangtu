"""initial schema

Revision ID: 070b7c13ab80
Revises:
Create Date: 2026-07-15 11:41:10.725852
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "070b7c13ab80"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", sa.String(length=100), nullable=True),
        sa.Column("detail_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_audit_logs_actor_created",
        "admin_audit_logs",
        ["actor_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_target", "admin_audit_logs", ["target_type", "target_id"], unique=False
    )
    op.create_table(
        "cosyvoice_voices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("voice_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("trait", sa.String(length=120), nullable=False),
        sa.Column("age_range", sa.String(length=40), nullable=False),
        sa.Column("languages", sa.Text(), nullable=False),
        sa.Column("supports_ssml", sa.Boolean(), nullable=False),
        sa.Column("supports_instruct", sa.Boolean(), nullable=False),
        sa.Column("supports_timestamp", sa.Boolean(), nullable=False),
        sa.Column("regions", sa.Text(), nullable=False),
        sa.Column("preview_audio_url", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_id", "voice_id", name="uq_cosyvoice_voices_model_voice"),
    )
    op.create_index(
        "ix_cosyvoice_voices_category_enabled",
        "cosyvoice_voices",
        ["category", "enabled"],
        unique=False,
    )
    op.create_index(
        "ix_cosyvoice_voices_model_enabled_sort",
        "cosyvoice_voices",
        ["model_id", "enabled", "sort_order"],
        unique=False,
    )
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scenario", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("settings_json", sa.Text(), nullable=True),
        sa.Column("source_images_json", sa.Text(), nullable=True),
        sa.Column("source_videos_json", sa.Text(), nullable=True),
        sa.Column("source_audios_json", sa.Text(), nullable=True),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("structure_json", sa.Text(), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "heygen_avatars",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("avatar_id", sa.String(length=128), nullable=False),
        sa.Column("group_id", sa.String(length=128), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("avatar_type", sa.String(length=32), nullable=False),
        sa.Column("ownership", sa.String(length=20), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("default_voice_id", sa.String(length=128), nullable=True),
        sa.Column("preferred_orientation", sa.String(length=20), nullable=True),
        sa.Column("preview_image_url", sa.Text(), nullable=True),
        sa.Column("preview_video_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("supported_api_engines_json", sa.Text(), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("avatar_id"),
    )
    op.create_index(
        "ix_heygen_avatars_enabled_sort", "heygen_avatars", ["enabled", "sort_order"], unique=False
    )
    op.create_index(
        "ix_heygen_avatars_type_enabled", "heygen_avatars", ["avatar_type", "enabled"], unique=False
    )
    op.create_table(
        "heygen_translation_languages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("display_name_zh", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_heygen_translation_languages_enabled_sort",
        "heygen_translation_languages",
        ["enabled", "sort_order"],
        unique=False,
    )
    op.create_index(
        "ix_heygen_translation_languages_provider_name",
        "heygen_translation_languages",
        ["provider", "name"],
        unique=False,
    )
    op.create_table(
        "heygen_voices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("voice_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("voice_type", sa.String(length=20), nullable=True),
        sa.Column("preview_audio_url", sa.Text(), nullable=True),
        sa.Column("support_locale", sa.Boolean(), nullable=False),
        sa.Column("support_pause", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("voice_id"),
    )
    op.create_index(
        "ix_heygen_voices_enabled_sort", "heygen_voices", ["enabled", "sort_order"], unique=False
    )
    op.create_index(
        "ix_heygen_voices_language_enabled", "heygen_voices", ["language", "enabled"], unique=False
    )
    op.create_table(
        "image_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column("replaced_by_task_id", sa.String(length=36), nullable=True),
        sa.Column("type_id", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("size", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("result_url", sa.String(length=500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_task_id", sa.String(length=128), nullable=True),
        sa.Column("credit_cost", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("credit_refunded", sa.Boolean(), nullable=False),
        sa.Column("prompt_snapshot_json", sa.Text(), nullable=True),
        sa.Column("settings_snapshot_json", sa.Text(), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "product_catalog",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scenario", sa.String(length=32), nullable=False),
        sa.Column("item_id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("strategy", sa.Text(), nullable=False),
        sa.Column("default_count", sa.Integer(), nullable=True),
        sa.Column("max_count", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario", "item_id", name="uq_product_catalog_scenario_item"),
    )
    op.create_index(
        "ix_product_catalog_lookup",
        "product_catalog",
        ["scenario", "enabled", "sort"],
        unique=False,
    )
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scenario", sa.String(length=32), nullable=True),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=True),
        sa.Column("type_id", sa.String(length=50), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prompt_templates_lookup",
        "prompt_templates",
        ["purpose", "model", "scenario", "platform", "type_id", "active"],
        unique=False,
    )
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "user_audio_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("audio_url", sa.Text(), nullable=False),
        sa.Column("object_key", sa.String(length=255), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_audio_assets_user_active",
        "user_audio_assets",
        ["user_id", "enabled", "archived_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_audio_assets_user_created",
        "user_audio_assets",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "user_avatar_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("avatar_type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("source_image_url", sa.Text(), nullable=False),
        sa.Column("source_object_key", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_task_id", sa.String(length=128), nullable=True),
        sa.Column("provider_avatar_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("credit_cost", sa.Integer(), nullable=False),
        sa.Column("credit_refunded", sa.Boolean(), nullable=False),
        sa.Column("result_avatar_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_avatar_tasks_provider_task",
        "user_avatar_tasks",
        ["provider_task_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_avatar_tasks_user_created",
        "user_avatar_tasks",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_avatar_tasks_user_status",
        "user_avatar_tasks",
        ["user_id", "status", "archived_at"],
        unique=False,
    )
    op.create_table(
        "user_avatars",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("avatar_type", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("heygen_avatar_id", sa.String(length=128), nullable=False),
        sa.Column("preview_image_url", sa.Text(), nullable=True),
        sa.Column("preview_video_url", sa.Text(), nullable=True),
        sa.Column("source_image_url", sa.Text(), nullable=False),
        sa.Column("source_object_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("heygen_avatar_id"),
    )
    op.create_index(
        "ix_user_avatars_heygen_avatar", "user_avatars", ["heygen_avatar_id"], unique=False
    )
    op.create_index(
        "ix_user_avatars_user_active",
        "user_avatars",
        ["user_id", "enabled", "archived_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_avatars_user_created", "user_avatars", ["user_id", "created_at"], unique=False
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("auth_version", sa.Integer(), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("consumption_multiplier", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("distribution_level", sa.Integer(), nullable=True),
        sa.Column("distribution_parent_id", sa.Integer(), nullable=True),
        sa.Column("commission_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("invite_code", sa.String(length=32), nullable=True),
        sa.Column("distribution_enabled", sa.Boolean(), nullable=False),
        sa.Column("commission_available_cents", sa.Integer(), nullable=False),
        sa.Column("commission_frozen_cents", sa.Integer(), nullable=False),
        sa.Column("commission_withdrawn_cents", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.String(length=32),
            server_default=sa.text("'user'::character varying"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'active'::character varying"),
            nullable=False,
        ),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "commission_available_cents >= 0 AND commission_frozen_cents >= 0 AND commission_withdrawn_cents >= 0",
            name="ck_users_commission_balances",
        ),
        sa.CheckConstraint(
            "commission_rate IS NULL OR (commission_rate >= 0 AND commission_rate <= 100)",
            name="ck_users_commission_rate",
        ),
        sa.CheckConstraint(
            "consumption_multiplier >= 0.01 AND consumption_multiplier <= 9.99",
            name="ck_users_consumption_multiplier",
        ),
        sa.CheckConstraint(
            "distribution_level IS NULL OR distribution_level IN (1, 2, 3)",
            name="ck_users_distribution_level",
        ),
        sa.ForeignKeyConstraint(
            ["distribution_parent_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(
        "ix_users_distribution_parent", "users", ["distribution_parent_id"], unique=False
    )
    op.create_index("ix_users_invite_code", "users", ["invite_code"], unique=True)
    op.create_table(
        "video_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column(
            "scenario",
            sa.String(length=32),
            server_default=sa.text("'product_video'::character varying"),
            nullable=False,
        ),
        sa.Column("type_id", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("input_mode", sa.String(length=32), nullable=False),
        sa.Column("input_images_json", sa.Text(), nullable=True),
        sa.Column("input_video_url", sa.Text(), nullable=True),
        sa.Column("audio_setting", sa.String(length=20), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("resolution", sa.String(length=20), nullable=False),
        sa.Column("aspect_ratio", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("result_url", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_task_id", sa.String(length=128), nullable=True),
        sa.Column("credit_cost", sa.Integer(), nullable=False),
        sa.Column("credit_refunded", sa.Boolean(), nullable=False),
        sa.Column("prompt_snapshot_json", sa.Text(), nullable=True),
        sa.Column("settings_snapshot_json", sa.Text(), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "voiceover_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("voice_id", sa.String(length=100), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("pitch", sa.Float(), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("instruction", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("provider_request_id", sa.String(length=128), nullable=True),
        sa.Column("usage_characters", sa.Integer(), nullable=True),
        sa.Column("credit_cost", sa.Integer(), nullable=False),
        sa.Column("credit_refunded", sa.Boolean(), nullable=False),
        sa.Column("result_asset_id", sa.String(length=36), nullable=True),
        sa.Column("settings_snapshot_json", sa.Text(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_voiceover_tasks_job_active_created",
        "voiceover_tasks",
        ["job_id", "archived", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_voiceover_tasks_user_status_created",
        "voiceover_tasks",
        ["user_id", "status", "created_at"],
        unique=False,
    )
    op.create_table(
        "commission_withdrawals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("alipay_name", sa.String(length=100), nullable=False),
        sa.Column("alipay_account", sa.String(length=150), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("reject_reason", sa.String(length=255), nullable=True),
        sa.Column("payment_reference", sa.String(length=100), nullable=True),
        sa.Column("voucher_url", sa.String(length=500), nullable=True),
        sa.Column("voucher_object_key", sa.String(length=500), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending_review', 'pending_payment', 'paid', 'rejected')",
            name="ck_commission_withdrawals_status",
        ),
        sa.CheckConstraint("amount_cents >= 10000", name="ck_commission_withdrawals_amount"),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commission_withdrawals_status_created",
        "commission_withdrawals",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_commission_withdrawals_user_created",
        "commission_withdrawals",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "coupon_codes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("credits >= 1 AND credits <= 10000000", name="ck_coupon_codes_credits"),
        sa.CheckConstraint(
            "usage_limit IS NULL OR (usage_limit > 0 AND usage_limit <= 1000000)",
            name="ck_coupon_codes_usage_limit",
        ),
        sa.CheckConstraint(
            "usage_limit IS NULL OR used_count <= usage_limit", name="ck_coupon_codes_usage_count"
        ),
        sa.CheckConstraint("used_count >= 0", name="ck_coupon_codes_used_count"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coupon_codes_code", "coupon_codes", ["code"], unique=True)
    op.create_index(
        "ix_coupon_codes_status", "coupon_codes", ["deleted_at", "enabled"], unique=False
    )
    op.create_table(
        "credit_orders",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("out_trade_no", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_trade_no", sa.String(length=64), nullable=True),
        sa.Column("package_id", sa.String(length=64), nullable=False),
        sa.Column("package_name", sa.String(length=100), nullable=False),
        sa.Column("package_snapshot_json", sa.Text(), nullable=False),
        sa.Column("distribution_snapshot_json", sa.Text(), nullable=True),
        sa.Column("distribution_root_user_id", sa.Integer(), nullable=True),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("pay_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("pay_url", sa.String(length=500), nullable=True),
        sa.Column("qr_code", sa.String(length=500), nullable=True),
        sa.Column("qr_img", sa.String(length=500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["distribution_root_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("out_trade_no", name="credit_orders_out_trade_no_key"),
    )
    op.create_index(
        "ix_credit_orders_distribution_root_status",
        "credit_orders",
        ["distribution_root_user_id", "status"],
        unique=False,
    )
    op.create_index("ix_credit_orders_out_trade_no", "credit_orders", ["out_trade_no"], unique=True)
    op.create_index(
        "ix_credit_orders_user_created", "credit_orders", ["user_id", "created_at"], unique=False
    )
    op.create_table(
        "outfit_models",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("object_key", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index(
        "ix_outfit_models_active_sort", "outfit_models", ["active", "sort_order"], unique=False
    )
    op.create_index(
        "ix_outfit_models_user_active_created",
        "outfit_models",
        ["user_id", "active", "created_at"],
        unique=False,
    )
    op.create_table(
        "commission_transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source_user_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.String(length=36), nullable=True),
        sa.Column("withdrawal_id", sa.String(length=36), nullable=True),
        sa.Column("type", sa.String(length=24), nullable=False),
        sa.Column("available_delta_cents", sa.Integer(), nullable=False),
        sa.Column("frozen_delta_cents", sa.Integer(), nullable=False),
        sa.Column("available_after_cents", sa.Integer(), nullable=False),
        sa.Column("frozen_after_cents", sa.Integer(), nullable=False),
        sa.Column("source_amount_cents", sa.Integer(), nullable=True),
        sa.Column("commission_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["credit_orders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["withdrawal_id"],
            ["commission_withdrawals.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commission_transactions_user_created",
        "commission_transactions",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "uq_commission_transactions_order_user_type",
        "commission_transactions",
        ["order_id", "user_id", "type"],
        unique=True,
    )
    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=True),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("credits_delta", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["credit_orders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_credit_transactions_order", "credit_transactions", ["order_id"], unique=False
    )
    op.create_index(
        "ix_credit_transactions_user_created",
        "credit_transactions",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_table(
        "coupon_redemptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("coupon_code_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_snapshot", sa.String(length=32), nullable=False),
        sa.Column("credits_snapshot", sa.Integer(), nullable=False),
        sa.Column("credit_transaction_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["coupon_code_id"],
            ["coupon_codes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["credit_transaction_id"],
            ["credit_transactions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("coupon_code_id", "user_id", name="uq_coupon_redemptions_coupon_user"),
        sa.UniqueConstraint("credit_transaction_id"),
    )
    op.create_index(
        "ix_coupon_redemptions_coupon_created",
        "coupon_redemptions",
        ["coupon_code_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_coupon_redemptions_user_created",
        "coupon_redemptions",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_coupon_redemptions_user_created", table_name="coupon_redemptions")
    op.drop_index("ix_coupon_redemptions_coupon_created", table_name="coupon_redemptions")
    op.drop_table("coupon_redemptions")
    op.drop_index("ix_credit_transactions_user_created", table_name="credit_transactions")
    op.drop_index("ix_credit_transactions_order", table_name="credit_transactions")
    op.drop_table("credit_transactions")
    op.drop_index(
        "uq_commission_transactions_order_user_type", table_name="commission_transactions"
    )
    op.drop_index("ix_commission_transactions_user_created", table_name="commission_transactions")
    op.drop_table("commission_transactions")
    op.drop_index("ix_outfit_models_user_active_created", table_name="outfit_models")
    op.drop_index("ix_outfit_models_active_sort", table_name="outfit_models")
    op.drop_table("outfit_models")
    op.drop_index("ix_credit_orders_user_created", table_name="credit_orders")
    op.drop_index("ix_credit_orders_out_trade_no", table_name="credit_orders")
    op.drop_index("ix_credit_orders_distribution_root_status", table_name="credit_orders")
    op.drop_table("credit_orders")
    op.drop_index("ix_coupon_codes_status", table_name="coupon_codes")
    op.drop_index("ix_coupon_codes_code", table_name="coupon_codes")
    op.drop_table("coupon_codes")
    op.drop_index("ix_commission_withdrawals_user_created", table_name="commission_withdrawals")
    op.drop_index("ix_commission_withdrawals_status_created", table_name="commission_withdrawals")
    op.drop_table("commission_withdrawals")
    op.drop_index("ix_voiceover_tasks_user_status_created", table_name="voiceover_tasks")
    op.drop_index("ix_voiceover_tasks_job_active_created", table_name="voiceover_tasks")
    op.drop_table("voiceover_tasks")
    op.drop_table("video_tasks")
    op.drop_index("ix_users_invite_code", table_name="users")
    op.drop_index("ix_users_distribution_parent", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_user_avatars_user_created", table_name="user_avatars")
    op.drop_index("ix_user_avatars_user_active", table_name="user_avatars")
    op.drop_index("ix_user_avatars_heygen_avatar", table_name="user_avatars")
    op.drop_table("user_avatars")
    op.drop_index("ix_user_avatar_tasks_user_status", table_name="user_avatar_tasks")
    op.drop_index("ix_user_avatar_tasks_user_created", table_name="user_avatar_tasks")
    op.drop_index("ix_user_avatar_tasks_provider_task", table_name="user_avatar_tasks")
    op.drop_table("user_avatar_tasks")
    op.drop_index("ix_user_audio_assets_user_created", table_name="user_audio_assets")
    op.drop_index("ix_user_audio_assets_user_active", table_name="user_audio_assets")
    op.drop_table("user_audio_assets")
    op.drop_table("system_settings")
    op.drop_index("ix_prompt_templates_lookup", table_name="prompt_templates")
    op.drop_table("prompt_templates")
    op.drop_index("ix_product_catalog_lookup", table_name="product_catalog")
    op.drop_table("product_catalog")
    op.drop_table("image_tasks")
    op.drop_index("ix_heygen_voices_language_enabled", table_name="heygen_voices")
    op.drop_index("ix_heygen_voices_enabled_sort", table_name="heygen_voices")
    op.drop_table("heygen_voices")
    op.drop_index(
        "ix_heygen_translation_languages_provider_name", table_name="heygen_translation_languages"
    )
    op.drop_index(
        "ix_heygen_translation_languages_enabled_sort", table_name="heygen_translation_languages"
    )
    op.drop_table("heygen_translation_languages")
    op.drop_index("ix_heygen_avatars_type_enabled", table_name="heygen_avatars")
    op.drop_index("ix_heygen_avatars_enabled_sort", table_name="heygen_avatars")
    op.drop_table("heygen_avatars")
    op.drop_table("generation_jobs")
    op.drop_index("ix_cosyvoice_voices_model_enabled_sort", table_name="cosyvoice_voices")
    op.drop_index("ix_cosyvoice_voices_category_enabled", table_name="cosyvoice_voices")
    op.drop_table("cosyvoice_voices")
    op.drop_index("ix_admin_audit_logs_target", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_actor_created", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
