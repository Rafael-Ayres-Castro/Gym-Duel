"""SQLAlchemy tables: users, workouts and weekly_goals."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
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
