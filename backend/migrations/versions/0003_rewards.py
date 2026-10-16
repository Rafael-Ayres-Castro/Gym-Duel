"""Phase 2 (C): rewards store and redemptions.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rewards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(80), nullable=False),
        sa.Column("cost", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rewards_created_by", "rewards", ["created_by"])

    op.create_table(
        "redemptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reward_id", sa.Integer(), sa.ForeignKey("rewards.id"), nullable=False),
        sa.Column("redeemed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("cost", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_redemptions_reward_id", "redemptions", ["reward_id"])
    op.create_index("ix_redemptions_redeemed_by", "redemptions", ["redeemed_by"])


def downgrade() -> None:
    op.drop_table("redemptions")
    op.drop_table("rewards")
