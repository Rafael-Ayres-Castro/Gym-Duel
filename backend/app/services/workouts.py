"""Check-in rules (allowed dates, daily limit), listing and deleting workouts."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import scoring
from ..config import Settings
from ..errors import api_error
from ..models import User, Workout
from ..schemas import WorkoutIn
from . import players, stats


def serialize(db: Session, workout: Workout) -> dict:
    return {
        "id": workout.id,
        "user_id": workout.user_id,
        "user_name": players.display_name(workout.user),
        "color": players.player_color(db, workout.user),
        "date": workout.date,
        "type": workout.type,
        "duration_min": workout.duration_min,
        "intensity": workout.intensity,
        "points": workout.points,
        "note": workout.note,
        "created_at": workout.created_at,
    }


def _check_allowed(db: Session, user: User, day: dt.date, today: dt.date, settings: Settings) -> None:
    if day not in (today, today - dt.timedelta(days=1)):
        raise api_error(422, "invalid_date", "O check-in só vale para hoje ou ontem.")
    stmt = select(func.count()).select_from(Workout).where(Workout.user_id == user.id, Workout.date == day)
    if (db.scalar(stmt) or 0) >= settings.max_workouts_per_day:
        raise api_error(409, "daily_limit", "Você já fez check-in neste dia.")


def create_checkin(db: Session, user: User, data: WorkoutIn, today: dt.date, settings: Settings) -> dict:
    """Store the workout and return it with the new scoreboard and the success-screen feedback."""
    _check_allowed(db, user, data.date, today, settings)
    me_before = stats.load_duel(db, user, today).me_week

    workout = Workout(
        user_id=user.id,
        date=data.date,
        type=data.type,
        duration_min=data.duration_min,
        intensity=data.intensity,
        points=scoring.calc_points(data.duration_min, data.intensity),
        note=data.note,
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)

    duel = stats.load_duel(db, user, today)
    # "Ontem" on a Monday lands in last week: it is saved but does not move this week's board.
    counts_for_current_week = data.date >= scoring.week_bounds(today)[0]
    feedback = scoring.checkin_feedback(
        me_before=me_before,
        me_after=duel.me_week,
        opponent=duel.opponent_week,
        counts_for_current_week=counts_for_current_week,
        streak_after=duel.me.streak(today),
        opponent_name=duel.opponent_name,
    )
    return {
        "workout": serialize(db, workout),
        "scoreboard": stats.build_scoreboard(db, duel),
        "feedback": {
            "message": feedback.message,
            "pill": feedback.pill,
            "counts_for_current_week": counts_for_current_week,
        },
    }


def list_workouts(
    db: Session, user: User, person: str, period: str, today: dt.date, limit: int | None
) -> list[dict]:
    stmt = select(Workout)
    if person == "me":
        stmt = stmt.where(Workout.user_id == user.id)
    elif person == "opponent":
        opponent = players.opponent_of(db, user)
        if opponent is None:
            return []
        stmt = stmt.where(Workout.user_id == opponent.id)

    start, end = stats.period_bounds(period, today)
    if start is not None:
        stmt = stmt.where(Workout.date >= start)
    stmt = stmt.where(Workout.date <= end).order_by(Workout.date.desc(), Workout.created_at.desc(), Workout.id.desc())
    if limit:
        stmt = stmt.limit(limit)
    return [serialize(db, w) for w in db.scalars(stmt)]


def delete_workout(db: Session, user: User, workout_id: int) -> None:
    """Delete one of the user's own workouts; its points go away with it."""
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise api_error(404, "not_found", "Treino não encontrado.")
    if workout.user_id != user.id:
        raise api_error(403, "forbidden", "Você só pode apagar os seus treinos.")
    db.delete(workout)
    db.commit()
