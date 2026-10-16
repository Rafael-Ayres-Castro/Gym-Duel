"""Phase 2 (A): workout photo flag, configurable rules, proposals, week results, badges, point ledger, notifications.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

RULE_COLUMNS = ("minutes_per_point", "intensity_adjust", "photo_bonus", "week_winner_bonus")


def upgrade() -> None:
    # The photo bonus is part of the rules, so workouts learn whether they have a photo now.
    with op.batch_alter_table("workouts") as batch:
        batch.add_column(sa.Column("photo_key", sa.String(200), nullable=True))

    op.create_table(
        "rule_proposals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proposed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        *(sa.Column(name, sa.Integer(), nullable=False) for name in RULE_COLUMNS),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_rule_proposals_status", "rule_proposals", ["status"])

    op.create_table(
        "scoring_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        *(sa.Column(name, sa.Integer(), nullable=False) for name in RULE_COLUMNS),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("proposal_id", sa.Integer(), sa.ForeignKey("rule_proposals.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scoring_rules_effective_from", "scoring_rules", ["effective_from"])

    op.create_table(
        "week_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("goal", sa.Integer(), nullable=False),
        sa.Column("done", sa.Integer(), nullable=False),
        sa.Column("pct", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("won_week", sa.Boolean(), nullable=False),
        sa.Column("streak_after", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "week_start"),
    )
    op.create_index("ix_week_results_user_id", "week_results", ["user_id"])
    op.create_index("ix_week_results_week_start", "week_results", ["week_start"])

    op.create_table(
        "streak_badges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("milestone", sa.Integer(), nullable=False),
        sa.Column("bonus", sa.Integer(), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "milestone"),
    )
    op.create_index("ix_streak_badges_user_id", "streak_badges", ["user_id"])

    op.create_table(
        "point_ledger",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("ref_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_point_ledger_user_id", "point_ledger", ["user_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("message", sa.String(200), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    for table in ("notifications", "point_ledger", "streak_badges", "week_results", "scoring_rules", "rule_proposals"):
        op.drop_table(table)
    with op.batch_alter_table("workouts") as batch:
        batch.drop_column("photo_key")
