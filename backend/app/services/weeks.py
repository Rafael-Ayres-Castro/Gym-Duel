"""Closing finished weeks: frozen results, streak badges and the week winner bonus.

There is no scheduler (a free host sleeps), so closing is lazy and idempotent:
every API request checks whether some finished week is still open and closes it.

A week only closes on Tuesday. On Monday, Sunday is still "ontem" and may get a
check-in, so closing earlier would freeze an incomplete week.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import scoring, texts
from ..models import StreakBadge, User, WeekResult, Workout
from ..scoring import WeekStats
from . import ledger, notifications, players, rules

WEEK = dt.timedelta(days=7)
CHECKIN_WINDOW_DAYS = 1  # check-ins are accepted for today and yesterday


def last_closable_week(today: dt.date) -> dt.date:
    """Monday of the latest week that can no longer receive check-ins."""
    oldest_open_day = today - dt.timedelta(days=CHECKIN_WINDOW_DAYS)
    last_closed_sunday = oldest_open_day - dt.timedelta(days=oldest_open_day.weekday() + 1)
    return last_closed_sunday - dt.timedelta(days=6)


def _week_stats(db: Session, user: User, week_start: dt.date, goal: int) -> WeekStats:
    stmt = select(Workout).where(
        Workout.user_id == user.id, Workout.date >= week_start, Workout.date <= week_start + dt.timedelta(days=6)
    )
    workouts = list(db.scalars(stmt))
    return WeekStats(user.id, len(workouts), goal, sum(w.points for w in workouts))


def _close_week(db: Session, week_start: dt.date, users: list[User], goals: dict, notify: bool) -> None:
    week_rules = rules.rules_for_week(db, week_start)
    closed: list[tuple[WeekResult, WeekStats]] = []
    for user in users:
        goal = players.goal_for_week(goals[user.id], week_start)
        if goal is None:  # user had not joined yet
            continue
        stats = _week_stats(db, user, week_start, goal)
        previous = db.scalar(select(WeekResult).where(WeekResult.user_id == user.id, WeekResult.week_start == week_start - WEEK))
        streak_after = ((previous.streak_after if previous else 0) + 1) if stats.goal_met else 0
        result = WeekResult(
            user_id=user.id, week_start=week_start, goal=goal, done=stats.done, pct=stats.pct,
            points=stats.points, won_week=False, streak_after=streak_after,
        )
        db.add(result)
        closed.append((result, stats))
        _award_badges(db, user, week_start, streak_after, notify)

    if len(closed) == 2:
        (result_a, stats_a), (result_b, stats_b) = closed
        winner_id = scoring.leader(stats_a, stats_b)
        if winner_id is not None:
            winner = result_a if winner_id == result_a.user_id else result_b
            winner.won_week = True
            db.flush()
            if week_rules.week_winner_bonus:
                ledger.add(db, winner_id, "week_win", week_rules.week_winner_bonus, winner.id)
                if notify:
                    notifications.notify(
                        db, winner_id, "week_won",
                        f"Você venceu a semana de {texts.week_range(week_start)}! +{week_rules.week_winner_bonus} pts no seu saldo.",
                    )


def _award_badges(db: Session, user: User, week_start: dt.date, streak_after: int, notify: bool) -> None:
    earned = set(db.scalars(select(StreakBadge.milestone).where(StreakBadge.user_id == user.id)))
    for milestone, bonus in scoring.badges_reached(streak_after, earned):
        badge = StreakBadge(user_id=user.id, milestone=milestone, bonus=bonus, week_start=week_start)
        db.add(badge)
        db.flush()
        ledger.add(db, user.id, "badge", bonus, badge.id)
        if notify:
            notifications.notify(
                db, user.id, "badge", f"Selo de {milestone} semanas seguidas com a meta batida! +{bonus} pts no seu saldo."
            )


def close_finished_weeks(db: Session, today: dt.date) -> None:
    last = last_closable_week(today)
    latest_closed = db.scalar(select(func.max(WeekResult.week_start)))
    if latest_closed is not None and latest_closed >= last:
        return  # fast path: nothing to do (almost every request)

    users = players.players_in_order(db)[:2]
    goals = {user.id: players.goals_by_week(db, user.id) for user in users}
    starts = [user_goals[0].week_start for user_goals in goals.values() if user_goals]
    if not starts:
        return
    week = latest_closed + WEEK if latest_closed else min(starts)
    try:
        while week <= last:
            # Only the most recent week notifies; older ones are a catch-up (e.g. first deploy).
            _close_week(db, week, users, goals, notify=week == last)
            db.commit()
            week += WEEK
    except IntegrityError:
        db.rollback()  # another request closed the same week first
