"""Check-ins: create, list with filters and delete your own."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..clock import get_today
from ..config import Settings, app_settings
from ..db import get_db
from ..models import User
from ..schemas import CheckinOut, Period, Person, WorkoutIn, WorkoutOut
from ..security import get_current_user
from ..services import workouts

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("", response_model=CheckinOut, status_code=status.HTTP_201_CREATED)
def create_workout(
    data: WorkoutIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(app_settings),
    today: dt.date = Depends(get_today),
):
    """Register a workout for today or yesterday. Points are computed here and stored."""
    return workouts.create_checkin(db, user, data, today, settings)


@router.get("", response_model=list[WorkoutOut])
def list_workouts(
    person: Person = Query("all", description="all, me (você) ou opponent (sua dupla)"),
    period: Period = Query("week", description="week (semana atual), month (mês atual) ou all"),
    limit: int | None = Query(None, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
):
    """Workouts of both players, newest first."""
    return workouts.list_workouts(db, user, person, period, today, limit)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete one of your own workouts (its points are removed with it)."""
    workouts.delete_workout(db, user, workout_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
