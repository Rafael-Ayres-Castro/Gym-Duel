"""Point balance: workout points (kept on `workouts`) plus ledger movements (bonuses and redemptions)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import PointLedger, Workout


def add(db: Session, user_id: int, source: str, amount: int, ref_id: int | None = None) -> PointLedger:
    entry = PointLedger(user_id=user_id, source=source, amount=amount, ref_id=ref_id)
    db.add(entry)
    return entry


def balance(db: Session, user_id: int) -> int:
    """Separate from the weekly scoreboard: it accumulates forever and redemptions lower it."""
    workouts = db.scalar(select(func.coalesce(func.sum(Workout.points), 0)).where(Workout.user_id == user_id))
    movements = db.scalar(select(func.coalesce(func.sum(PointLedger.amount), 0)).where(PointLedger.user_id == user_id))
    return int(workouts) + int(movements)
