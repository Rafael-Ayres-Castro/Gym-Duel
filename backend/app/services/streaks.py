"""Streak panel of "Metas e regras": current streak, record, last 9 weeks and badges per player."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import scoring
from ..models import StreakBadge
from . import players
from .stats import Duel, PlayerHistory

GRID_WEEKS = 9  # 8 closed weeks + the current one, as in the prototype
WEEK = dt.timedelta(days=7)


def _weeks_grid(history: PlayerHistory, today: dt.date) -> list[dict]:
    current = scoring.week_bounds(today)[0]
    grid = []
    for offset in range(GRID_WEEKS - 1, -1, -1):
        week_start = current - offset * WEEK
        stats = history.week(week_start)
        grid.append(
            {
                "week_start": week_start,
                "is_current": offset == 0,
                "goal": stats.goal if stats else None,
                "done": stats.done if stats else 0,
                "met": bool(stats and stats.goal_met),
            }
        )
    return grid


def _player_streaks(db: Session, history: PlayerHistory, today: dt.date, is_me: bool) -> dict:
    earned = set(db.scalars(select(StreakBadge.milestone).where(StreakBadge.user_id == history.user.id)))
    streak = history.streak(today)
    upcoming = scoring.next_badge(streak, earned)
    return {
        "user_id": history.user.id,
        "name": players.display_name(history.user),
        "color": players.player_color(db, history.user),
        "is_me": is_me,
        "streak": streak,
        "record": history.record(today),
        "weeks": _weeks_grid(history, today),
        "badges": [
            {"milestone": milestone, "bonus": bonus, "earned": milestone in earned} for milestone, bonus in scoring.BADGES
        ],
        "next_badge": {"milestone": upcoming[0], "weeks_left": upcoming[1]} if upcoming else None,
    }


def build_streaks(db: Session, duel: Duel) -> dict:
    histories = [(duel.me, True)] + ([(duel.opponent, False)] if duel.opponent else [])
    return {"players": [_player_streaks(db, history, duel.today, is_me) for history, is_me in histories]}
