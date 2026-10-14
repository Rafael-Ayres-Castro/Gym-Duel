"""Week numbers, streaks, scoreboard and period summaries built from the database.

The data set is tiny (two people), so each player's full history is loaded once
and the pure functions in `scoring` do the math in memory.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import scoring
from ..models import User, WeeklyGoal, Workout
from ..scoring import WeekStats
from . import players

WEEK = dt.timedelta(days=7)


@dataclass
class PlayerHistory:
    user: User
    goals: list[WeeklyGoal]
    workouts: list[Workout]
    by_week: dict[dt.date, list[Workout]] = field(init=False)

    def __post_init__(self) -> None:
        self.by_week = {}
        for workout in self.workouts:
            week_start = scoring.week_bounds(workout.date)[0]
            self.by_week.setdefault(week_start, []).append(workout)

    def week(self, week_start: dt.date) -> WeekStats | None:
        """Stats for one week, or None when the user had no goal yet that week."""
        goal = players.goal_for_week(self.goals, week_start)
        if goal is None:
            return None
        workouts = self.by_week.get(week_start, [])
        return WeekStats(self.user.id, len(workouts), goal, sum(w.points for w in workouts))

    def current_week(self, today: dt.date) -> WeekStats:
        week_start = scoring.week_bounds(today)[0]
        stats = self.week(week_start)
        if stats is None:  # Goal rows are created at sign up, so this is only a safety net.
            workouts = self.by_week.get(week_start, [])
            stats = WeekStats(self.user.id, len(workouts), 1, sum(w.points for w in workouts))
        return stats

    def _closed_weeks_met(self, today: dt.date) -> Iterator[bool]:
        """Closed weeks, most recent first, until the user's first goal."""
        if not self.goals:
            return
        first_week = self.goals[0].week_start
        week_start = scoring.week_bounds(today)[0] - WEEK
        while week_start >= first_week:
            stats = self.week(week_start)
            yield stats is not None and stats.goal_met
            week_start -= WEEK

    def streak(self, today: dt.date) -> int:
        return scoring.streak(self._closed_weeks_met(today), self.current_week(today).goal_met)

    def days_trained(self, week_start: dt.date) -> list[bool]:
        dates = {w.date for w in self.by_week.get(week_start, [])}
        return [week_start + dt.timedelta(days=i) in dates for i in range(7)]


def load_history(db: Session, user: User) -> PlayerHistory:
    workouts = list(db.scalars(select(Workout).where(Workout.user_id == user.id)))
    return PlayerHistory(user, players.goals_by_week(db, user.id), workouts)


@dataclass
class Duel:
    """The logged user and their opponent (if any), with this week's numbers."""

    me: PlayerHistory
    opponent: PlayerHistory | None
    today: dt.date

    @property
    def me_week(self) -> WeekStats:
        return self.me.current_week(self.today)

    @property
    def opponent_week(self) -> WeekStats | None:
        return self.opponent.current_week(self.today) if self.opponent else None

    @property
    def opponent_name(self) -> str:
        return players.display_name(self.opponent.user) if self.opponent else ""


def load_duel(db: Session, me: User, today: dt.date) -> Duel:
    opponent = players.opponent_of(db, me)
    return Duel(load_history(db, me), load_history(db, opponent) if opponent else None, today)


def _player_out(db: Session, history: PlayerHistory, today: dt.date, is_me: bool, leader_id: int | None) -> dict:
    stats = history.current_week(today)
    return {
        "user_id": history.user.id,
        "name": players.display_name(history.user),
        "color": players.player_color(db, history.user),
        "is_me": is_me,
        "done": stats.done,
        "goal": stats.goal,
        "pct": stats.pct,
        "points": stats.points,
        "streak": history.streak(today),
        "is_leader": leader_id == history.user.id,
        "days": history.days_trained(scoring.week_bounds(today)[0]),
    }


def build_scoreboard(db: Session, duel: Duel) -> dict:
    me_week, opponent_week = duel.me_week, duel.opponent_week
    leader_id = scoring.leader(me_week, opponent_week)
    week_start, week_end = scoring.week_bounds(duel.today)
    player_rows = [_player_out(db, duel.me, duel.today, True, leader_id)]
    if duel.opponent:
        player_rows.append(_player_out(db, duel.opponent, duel.today, False, leader_id))
    return {
        "today": duel.today,
        "week_start": week_start,
        "week_end": week_end,
        "players": player_rows,
        "leader_id": leader_id,
        "duel_message": scoring.duel_message(me_week, opponent_week, duel.opponent_name),
        "waiting_for_opponent": duel.opponent is None,
    }


def period_bounds(period: str, today: dt.date) -> tuple[dt.date | None, dt.date]:
    """First and last day of a history period: this week, this month (so far) or everything."""
    if period == "week":
        return scoring.week_bounds(today)[0], today
    if period == "month":
        return today.replace(day=1), today
    return None, today


def build_summary(db: Session, duel: Duel, period: str) -> dict:
    start, end = period_bounds(period, duel.today)
    histories = [duel.me] + ([duel.opponent] if duel.opponent else [])
    rows = []
    for history in histories:
        in_period = [w for w in history.workouts if (start is None or w.date >= start) and w.date <= end]
        rows.append(
            {
                "user_id": history.user.id,
                "name": players.display_name(history.user),
                "color": players.player_color(db, history.user),
                "is_me": history is duel.me,
                "workouts": len(in_period),
                "points": sum(w.points for w in in_period),
                "pct": history.current_week(duel.today).pct,
            }
        )
    return {"period": period, "start": start, "end": end, "players": rows}
