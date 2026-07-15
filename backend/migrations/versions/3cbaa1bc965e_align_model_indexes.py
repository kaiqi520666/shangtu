"""align model indexes

Revision ID: 3cbaa1bc965e
Revises: 070b7c13ab80
Create Date: 2026-07-15 11:52:16.580215
"""

from collections.abc import Sequence

from alembic import op


revision: str = "3cbaa1bc965e"
down_revision: str | Sequence[str] | None = "070b7c13ab80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(op.f("credit_orders_out_trade_no_key"), "credit_orders", type_="unique")
    op.create_index(
        "ix_generation_jobs_user_scenario_active_created",
        "generation_jobs",
        ["user_id", "scenario", "archived", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_image_tasks_job_active_current",
        "image_tasks",
        ["job_id", "user_id", "archived", "replaced_by_task_id"],
        unique=False,
    )
    op.create_index(
        "ix_image_tasks_status_created", "image_tasks", ["status", "created_at"], unique=False
    )
    op.create_index(
        "ix_image_tasks_user_active_created",
        "image_tasks",
        ["user_id", "archived", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_video_tasks_job_user_active_scenario",
        "video_tasks",
        ["job_id", "user_id", "archived", "scenario"],
        unique=False,
    )
    op.create_index(
        "ix_video_tasks_status_created", "video_tasks", ["status", "created_at"], unique=False
    )
    op.create_index(
        "ix_video_tasks_user_active_status_scenario_created",
        "video_tasks",
        ["user_id", "archived", "status", "scenario", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_video_tasks_user_active_status_scenario_created", table_name="video_tasks")
    op.drop_index("ix_video_tasks_status_created", table_name="video_tasks")
    op.drop_index("ix_video_tasks_job_user_active_scenario", table_name="video_tasks")
    op.drop_index("ix_image_tasks_user_active_created", table_name="image_tasks")
    op.drop_index("ix_image_tasks_status_created", table_name="image_tasks")
    op.drop_index("ix_image_tasks_job_active_current", table_name="image_tasks")
    op.drop_index("ix_generation_jobs_user_scenario_active_created", table_name="generation_jobs")
    op.create_unique_constraint(
        op.f("credit_orders_out_trade_no_key"),
        "credit_orders",
        ["out_trade_no"],
        postgresql_nulls_not_distinct=False,
    )
