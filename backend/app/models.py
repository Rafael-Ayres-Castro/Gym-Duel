"""SQLAlchemy tables: users, workouts and weekly_goals."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    workouts: Mapped[list[Workout]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list[WeeklyGoal]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    type: Mapped[str] = mapped_column(String(20))
    duration_min: Mapped[int] = mapped_column(Integer)
    intensity: Mapped[str] = mapped_column(String(10))
    # Stored at check-in time so later rule changes never rewrite past scores.
    points: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String(140), default="")
    # Storage key of the proof photo (never a public URL); None = no photo.
    photo_key: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="workouts")


class WeeklyGoal(Base):
    """Goal valid from `week_start` until the next row of the same user.

    Keeping one row per change (instead of a column on users) lets the goal
    change from this week on without rewriting past weeks' results.
    """

    __tablename__ = "weekly_goals"
    __table_args__ = (UniqueConstraint("user_id", "week_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    week_start: Mapped[dt.date] = mapped_column(Date)
    goal: Mapped[int] = mapped_column(Integer)

    user: Mapped[User] = relationship(back_populates="goals")


class ScoringRules(Base):
    """One version of the scoring rules, in force from `effective_from` (a Monday) on.

    Versions are append-only: the latest version starting on or before a week is
    the one used for that week, so closed weeks keep the rules they were played with.
    """

    __tablename__ = "scoring_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    minutes_per_point: Mapped[int] = mapped_column(Integer)
    intensity_adjust: Mapped[int] = mapped_column(Integer)
    photo_bonus: Mapped[int] = mapped_column(Integer)
    week_winner_bonus: Mapped[int] = mapped_column(Integer)
    effective_from: Mapped[dt.date] = mapped_column(Date, index=True)
    proposal_id: Mapped[int | None] = mapped_column(ForeignKey("rule_proposals.id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RuleProposal(Base):
    """A change of rules waiting for the other member: pending → approved | rejected | cancelled."""

    __tablename__ = "rule_proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    proposed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    minutes_per_point: Mapped[int] = mapped_column(Integer)
    intensity_adjust: Mapped[int] = mapped_column(Integer)
    photo_bonus: Mapped[int] = mapped_column(Integer)
    week_winner_bonus: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="pending", index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class WeekResult(Base):
    """Frozen outcome of a closed week for one player (written once, when the week closes)."""

    __tablename__ = "week_results"
    __table_args__ = (UniqueConstraint("user_id", "week_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    week_start: Mapped[dt.date] = mapped_column(Date, index=True)
    goal: Mapped[int] = mapped_column(Integer)
    done: Mapped[int] = mapped_column(Integer)
    pct: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer)
    won_week: Mapped[bool] = mapped_column(Boolean, default=False)
    streak_after: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StreakBadge(Base):
    """A streak milestone (2, 4, 8, 12 weeks) earned once per player."""

    __tablename__ = "streak_badges"
    __table_args__ = (UniqueConstraint("user_id", "milestone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    milestone: Mapped[int] = mapped_column(Integer)
    bonus: Mapped[int] = mapped_column(Integer)
    week_start: Mapped[dt.date] = mapped_column(Date)
    awarded_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PointLedger(Base):
    """Balance movements other than workouts: bonuses (positive) and redemptions (negative).

    balance = sum of the user's workout points + sum of their ledger amounts.
    Workout points stay only on `workouts`, because approving new rules recalculates them.
    """

    __tablename__ = "point_ledger"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    source: Mapped[str] = mapped_column(String(20))  # badge | week_win | challenge | redemption
    ref_id: Mapped[int | None] = mapped_column(Integer)
    amount: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    """Short message for one user, shown as a toast the next time they open the app."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class Reward(Base):
    """Something the creator offers; only the other member redeems it, paying with points."""

    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(80))
    cost: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Redemption(Base):
    """A redeemed reward: pending → fulfilled (by the owner) → received (by who redeemed)."""

    __tablename__ = "redemptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    reward_id: Mapped[int] = mapped_column(ForeignKey("rewards.id"), index=True)
    redeemed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    cost: Mapped[int] = mapped_column(Integer)  # price at the moment of the redemption
    status: Mapped[str] = mapped_column(String(10), default="pending")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    fulfilled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    reward: Mapped[Reward] = relationship()


class Challenge(Base):
    """A side bet between the two: pending → active (accepted) → done. Declined/cancelled ones are deleted.

    Progress is never stored: it is always derived from the workouts inside the period.
    """

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    challenged_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(10))  # count | minutes | goal
    workout_type: Mapped[str | None] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(10))  # week | weekend
    starts_on: Mapped[dt.date] = mapped_column(Date)
    ends_on: Mapped[dt.date] = mapped_column(Date, index=True)
    stake_points: Mapped[int | None] = mapped_column(Integer)
    stake_text: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(10), default="pending", index=True)
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    accepted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
