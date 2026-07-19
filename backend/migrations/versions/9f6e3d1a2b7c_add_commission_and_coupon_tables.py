"""add commission and coupon tables

Revision ID: 9f6e3d1a2b7c
Revises: 3cbaa1bc965e
Create Date: 2026-07-19 17:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "9f6e3d1a2b7c"
down_revision: str | Sequence[str] | None = "3cbaa1bc965e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("auth_version", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column("consumption_multiplier", sa.Numeric(3, 2), nullable=True),
    )
    op.add_column("users", sa.Column("distribution_level", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column("distribution_parent_id", sa.Integer(), nullable=True),
    )
    op.add_column("users", sa.Column("commission_rate", sa.Numeric(5, 2), nullable=True))
    op.add_column("users", sa.Column("invite_code", sa.String(32), nullable=True))
    op.add_column(
        "users",
        sa.Column("distribution_enabled", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("commission_available_cents", sa.Integer(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("commission_frozen_cents", sa.Integer(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("commission_withdrawn_cents", sa.Integer(), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE users SET auth_version = 0, consumption_multiplier = 1.00, "
            "distribution_enabled = false, commission_available_cents = 0, "
            "commission_frozen_cents = 0, commission_withdrawn_cents = 0"
        )
    )
    for name in (
        "auth_version",
        "consumption_multiplier",
        "distribution_enabled",
        "commission_available_cents",
        "commission_frozen_cents",
        "commission_withdrawn_cents",
    ):
        op.alter_column("users", name, nullable=False)
    op.create_foreign_key(
        "fk_users_distribution_parent_id_users",
        "users",
        "users",
        ["distribution_parent_id"],
        ["id"],
    )
    op.create_index("ix_users_distribution_parent", "users", ["distribution_parent_id"])
    op.create_index("ix_users_invite_code", "users", ["invite_code"], unique=True)

    op.add_column("credit_orders", sa.Column("distribution_snapshot_json", sa.Text(), nullable=True))
    op.add_column(
        "credit_orders",
        sa.Column("distribution_root_user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_credit_orders_distribution_root_user_id_users",
        "credit_orders",
        "users",
        ["distribution_root_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_credit_orders_distribution_root_status",
        "credit_orders",
        ["distribution_root_user_id", "status"],
    )

    op.create_table(
        "commission_withdrawals",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("alipay_name", sa.String(100), nullable=False),
        sa.Column("alipay_account", sa.String(150), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("reject_reason", sa.String(255), nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("voucher_url", sa.String(500), nullable=True),
        sa.Column("voucher_object_key", sa.String(500), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount_cents >= 10000", name="ck_commission_withdrawals_amount"),
        sa.CheckConstraint(
            "status IN ('pending_review', 'pending_payment', 'paid', 'rejected')",
            name="ck_commission_withdrawals_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_commission_withdrawals_user_created",
        "commission_withdrawals",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_commission_withdrawals_status_created",
        "commission_withdrawals",
        ["status", "created_at"],
    )

    op.create_table(
        "commission_transactions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("source_user_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.String(36), nullable=True),
        sa.Column("withdrawal_id", sa.String(36), nullable=True),
        sa.Column("type", sa.String(24), nullable=False),
        sa.Column("available_delta_cents", sa.Integer(), nullable=False),
        sa.Column("frozen_delta_cents", sa.Integer(), nullable=False),
        sa.Column("available_after_cents", sa.Integer(), nullable=False),
        sa.Column("frozen_after_cents", sa.Integer(), nullable=False),
        sa.Column("source_amount_cents", sa.Integer(), nullable=True),
        sa.Column("commission_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["credit_orders.id"]),
        sa.ForeignKeyConstraint(["source_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["withdrawal_id"], ["commission_withdrawals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id",
            "user_id",
            "type",
            name="uq_commission_transactions_order_user_type",
        ),
    )
    op.create_index(
        "ix_commission_transactions_user_created",
        "commission_transactions",
        ["user_id", "created_at"],
    )

    op.create_table(
        "coupon_codes",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
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
        sa.CheckConstraint("used_count >= 0", name="ck_coupon_codes_used_count"),
        sa.CheckConstraint(
            "usage_limit IS NULL OR used_count <= usage_limit",
            name="ck_coupon_codes_usage_count",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coupon_codes_code", "coupon_codes", ["code"], unique=True)
    op.create_index("ix_coupon_codes_status", "coupon_codes", ["deleted_at", "enabled"])

    op.create_table(
        "coupon_redemptions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("coupon_code_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_snapshot", sa.String(32), nullable=False),
        sa.Column("credits_snapshot", sa.Integer(), nullable=False),
        sa.Column("credit_transaction_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["coupon_code_id"], ["coupon_codes.id"]),
        sa.ForeignKeyConstraint(["credit_transaction_id"], ["credit_transactions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("coupon_code_id", "user_id", name="uq_coupon_redemptions_coupon_user"),
        sa.UniqueConstraint("credit_transaction_id"),
    )
    op.create_index(
        "ix_coupon_redemptions_user_created",
        "coupon_redemptions",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_coupon_redemptions_coupon_created",
        "coupon_redemptions",
        ["coupon_code_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("coupon_redemptions")
    op.drop_table("coupon_codes")
    op.drop_table("commission_transactions")
    op.drop_table("commission_withdrawals")
    op.drop_index("ix_credit_orders_distribution_root_status", table_name="credit_orders")
    op.drop_constraint(
        "fk_credit_orders_distribution_root_user_id_users", "credit_orders", type_="foreignkey"
    )
    op.drop_column("credit_orders", "distribution_root_user_id")
    op.drop_column("credit_orders", "distribution_snapshot_json")
    op.drop_index("ix_users_invite_code", table_name="users")
    op.drop_index("ix_users_distribution_parent", table_name="users")
    op.drop_constraint("fk_users_distribution_parent_id_users", "users", type_="foreignkey")
    for name in (
        "commission_withdrawn_cents",
        "commission_frozen_cents",
        "commission_available_cents",
        "distribution_enabled",
        "invite_code",
        "commission_rate",
        "distribution_parent_id",
        "distribution_level",
        "consumption_multiplier",
        "auth_version",
    ):
        op.drop_column("users", name)
