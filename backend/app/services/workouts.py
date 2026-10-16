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
from ..scoring import WeekStats
from ..storage import PhotoStorage
from . import players, rules, stats


def serialize(db: Session, workout: Workout, storage: PhotoStorage) -> dict:
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
        "has_photo": bool(workout.photo_key),
        "photo_url": storage.signed_url(workout.photo_key) if workout.photo_key else None,
        "created_at": workout.created_at,
    }


def in_checkin_window(day: dt.date, today: dt.date) -> bool:
    """Check-ins (and deletions) only touch today or yesterday, so closed weeks never change."""
    return day in (today, today - dt.timedelta(days=1))


def _check_allowed(db: Session, user: User, day: dt.date, today: dt.date, settings: Settings) -> None:
    if not in_checkin_window(day, today):
        raise api_error(422, "invalid_date", "O check-in só vale para hoje ou ontem.")
    stmt = select(func.count()).select_from(Workout).where(Workout.user_id == user.id, Workout.date == day)
    if (db.scalar(stmt) or 0) >= settings.max_workouts_per_day:
        raise api_error(409, "daily_limit", "Você já fez check-in neste dia.")


def create_checkin(
    db: Session, user: User, data: WorkoutIn, today: dt.date, settings: Settings, storage: PhotoStorage
) -> dict:
    """Store the workout and return it with the new scoreboard and the success-screen feedback."""
    _check_allowed(db, user, data.date, today, settings)
    workout = Workout(
        user_id=user.id,
        date=data.date,
        type=data.type,
        duration_min=data.duration_min,
        intensity=data.intensity,
        points=scoring.calc_points(data.duration_min, data.intensity, False, rules.rules_for_date(db, data.date)),
        note=data.note,
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return checkin_result(db, user, workout, today, storage)


def checkin_result(db: Session, user: User, workout: Workout, today: dt.date, storage: PhotoStorage) -> dict:
    """Workout + new scoreboard + feedback comparing the board with and without this workout.

    Also used after a photo is attached, since the photo bonus changes the points.
    """
    duel = stats.load_duel(db, user, today)
    me_after = duel.me_week
    # "Ontem" on a Monday lands in last week: it is saved but does not move this week's board.
    counts_for_current_week = workout.date >= scoring.week_bounds(today)[0]
    me_before = (
        WeekStats(me_after.user_id, me_after.done - 1, me_after.goal, me_after.points - workout.points)
        if counts_for_current_week
        else me_after
    )
    feedback = scoring.checkin_feedback(
        me_before=me_before,
        me_after=me_after,
        opponent=duel.opponent_week,
        counts_for_current_week=counts_for_current_week,
        streak_after=duel.me.streak(today),
        opponent_name=duel.opponent_name,
    )
    return {
        "workout": serialize(db, workout, storage),
        "scoreboard": stats.build_scoreboard(db, duel),
        "feedback": {
            "message": feedback.message,
            "pill": feedback.pill,
            "counts_for_current_week": counts_for_current_week,
        },
    }


def list_workouts(
    db: Session, user: User, person: str, period: str, today: dt.date, limit: int | None, storage: PhotoStorage
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
    return [serialize(db, w, storage) for w in db.scalars(stmt)]


def own_recent_workout(db: Session, user: User, workout_id: int, today: dt.date, action: str) -> Workout:
    """A workout of the user that can still change (today or yesterday)."""
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise api_error(404, "not_found", "Treino não encontrado.")
    if workout.user_id != user.id:
        raise api_error(403, "forbidden", f"Você só pode {action} os seus treinos.")
    if not in_checkin_window(workout.date, today):
        raise api_error(409, "too_old", f"Só dá para {action} treinos de hoje ou de ontem.")
    return workout


def delete_workout(db: Session, user: User, workout_id: int, today: dt.date, storage: PhotoStorage) -> None:
    """Delete one of the user's own recent workouts; its points (and photo) go away with it."""
    workout = own_recent_workout(db, user, workout_id, today, "apagar")
    photo_key = workout.photo_key
    db.delete(workout)
    db.commit()
    if photo_key:
        storage.delete(photo_key)
