"""Phase 2 (D): challenges between the two members.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("challenged_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("workout_type", sa.String(20), nullable=True),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("stake_points", sa.Integer(), nullable=True),
        sa.Column("stake_text", sa.String(120), nullable=True),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("winner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_challenges_created_by", "challenges", ["created_by"])
    op.create_index("ix_challenges_challenged_id", "challenges", ["challenged_id"])
    op.create_index("ix_challenges_ends_on", "challenges", ["ends_on"])
    op.create_index("ix_challenges_status", "challenges", ["status"])


def downgrade() -> None:
    op.drop_table("challenges")
