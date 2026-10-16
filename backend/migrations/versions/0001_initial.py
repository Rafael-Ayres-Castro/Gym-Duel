"""MVP schema: users, workouts and weekly_goals.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "workouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("intensity", sa.String(10), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(140), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"])
    op.create_index("ix_workouts_date", "workouts", ["date"])

    op.create_table(
        "weekly_goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("goal", sa.Integer(), nullable=False),
        sa.UniqueConstraint("user_id", "week_start"),
    )
    op.create_index("ix_weekly_goals_user_id", "weekly_goals", ["user_id"])


def downgrade() -> None:
    op.drop_table("weekly_goals")
    op.drop_table("workouts")
    op.drop_table("users")
