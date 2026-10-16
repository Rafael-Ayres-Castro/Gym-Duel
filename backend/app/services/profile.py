"""All-time numbers of one player for the account screen (GET /me/stats).

Everything is derived from data that already exists (workouts, closed weeks, ledger,
badges, challenges and redemptions); nothing new is stored.
"""

from __future__ import annotations

import datetime as dt
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Challenge, PointLedger, Redemption, StreakBadge, User, WeekResult
from . import stats


def _count(db: Session, model: type, *conditions) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0


def _favorite_type(workout_types: list[str]) -> str | None:
    """Most registered workout type; on a tie, the one reached first wins (stable order)."""
    if not workout_types:
        return None
    return Counter(workout_types).most_common(1)[0][0]


def _ledger_totals(db: Session, user_id: int) -> tuple[int, int]:
    """(bonuses received, points spent) from the ledger; spent is returned as a positive number."""
    amounts = list(db.scalars(select(PointLedger.amount).where(PointLedger.user_id == user_id)))
    bonuses = sum(amount for amount in amounts if amount > 0)
    spent = -sum(amount for amount in amounts if amount < 0)
    return bonuses, spent


def build_profile_stats(db: Session, user: User, today: dt.date) -> dict:
    history = stats.load_history(db, user)
    workouts = sorted(history.workouts, key=lambda w: (w.date, w.id))
    bonuses, spent = _ledger_totals(db, user.id)
    return {
        "workouts": len(workouts),
        "minutes": sum(w.duration_min for w in workouts),
        "favorite_type": _favorite_type([w.type for w in workouts]),
        "points_earned": sum(w.points for w in workouts) + bonuses,
        "points_spent": spent,
        "weeks_closed": _count(db, WeekResult, WeekResult.user_id == user.id),
        "weeks_won": _count(db, WeekResult, WeekResult.user_id == user.id, WeekResult.won_week.is_(True)),
        "weeks_goal_met": _count(db, WeekResult, WeekResult.user_id == user.id, WeekResult.done >= WeekResult.goal),
        "streak": history.streak(today),
        "record": history.record(today),
        "badges": _count(db, StreakBadge, StreakBadge.user_id == user.id),
        "challenges_won": _count(db, Challenge, Challenge.winner_id == user.id),
        "rewards_redeemed": _count(db, Redemption, Redemption.redeemed_by == user.id),
    }
