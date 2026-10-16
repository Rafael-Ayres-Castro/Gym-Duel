"""Who plays against whom, player colors and weekly goals."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..models import User, WeeklyGoal
from ..scoring import first_name, week_bounds
from . import ledger

COLORS = ("blue", "pink")


def count_users(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User)) or 0


def players_in_order(db: Session) -> list[User]:
    """All users by registration order (the order decides the colors)."""
    return list(db.scalars(select(User).order_by(User.id)))


def player_color(db: Session, user: User) -> str:
    """First registered user is blue, the second is pink (fixed, so each person keeps their color)."""
    position = db.scalar(select(func.count()).select_from(User).where(User.id < user.id)) or 0
    return COLORS[position % len(COLORS)]


def opponent_of(db: Session, user: User) -> User | None:
    return db.scalar(select(User).where(User.id != user.id).order_by(User.id).limit(1))


def display_name(user: User) -> str:
    return first_name(user.name)


def user_out(db: Session, user: User, today: dt.date) -> dict:
    week_start = week_bounds(today)[0]
    return {
        "id": user.id,
        "name": user.name,
        "first_name": display_name(user),
        "email": user.email,
        "weekly_goal": current_goal(db, user.id, week_start),
        "next_weekly_goal": next_goal(db, user.id, week_start),
        "balance": ledger.balance(db, user.id),
        "color": player_color(db, user),
        "created_at": user.created_at,
    }


# ---- Weekly goals ----


def goals_by_week(db: Session, user_id: int) -> list[WeeklyGoal]:
    stmt = select(WeeklyGoal).where(WeeklyGoal.user_id == user_id).order_by(WeeklyGoal.week_start)
    return list(db.scalars(stmt))


def goal_for_week(goals: list[WeeklyGoal], week_start: dt.date) -> int | None:
    """Goal in force on `week_start`: the latest change made on or before it.

    `goals` must be sorted by week_start. None means the user had no goal yet
    (the week is before they joined).
    """
    current = None
    for goal in goals:
        if goal.week_start > week_start:
            break
        current = goal.goal
    return current


def current_goal(db: Session, user_id: int, week_start: dt.date) -> int:
    """Goal in force in the given week."""
    return goal_for_week(goals_by_week(db, user_id), week_start) or 1


def next_goal(db: Session, user_id: int, week_start: dt.date) -> int | None:
    """Goal already scheduled for a coming week, if it differs from this week's."""
    stmt = select(WeeklyGoal.goal).where(WeeklyGoal.user_id == user_id, WeeklyGoal.week_start > week_start)
    scheduled = db.scalar(stmt.order_by(WeeklyGoal.week_start.desc()).limit(1))
    return scheduled if scheduled is not None and scheduled != current_goal(db, user_id, week_start) else None


def set_goal(db: Session, user_id: int, goal: int, week_start: dt.date) -> None:
    """Set the goal from `week_start` on; past weeks keep the goal they had."""
    stmt = select(WeeklyGoal).where(WeeklyGoal.user_id == user_id, WeeklyGoal.week_start == week_start)
    row = db.scalar(stmt)
    if row is None:
        db.add(WeeklyGoal(user_id=user_id, week_start=week_start, goal=goal))
    else:
        row.goal = goal


def schedule_goal(db: Session, user_id: int, goal: int, today: dt.date) -> None:
    """Change the goal from next week on, so the scoreboard of the week in course never moves.

    Choosing the goal already in force simply drops any change scheduled before.
    """
    week_start = week_bounds(today)[0]
    db.execute(delete(WeeklyGoal).where(WeeklyGoal.user_id == user_id, WeeklyGoal.week_start > week_start))
    if goal != current_goal(db, user_id, week_start):
        set_goal(db, user_id, goal, week_start + dt.timedelta(days=7))
