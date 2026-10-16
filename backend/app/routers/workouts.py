"""Check-ins: create, list with filters and delete your own."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from ..clock import get_today
from ..config import Settings, app_settings
from ..db import get_db
from ..models import User
from ..schemas import CheckinOut, Period, Person, WorkoutIn, WorkoutOut
from ..security import get_current_user
from ..services import photos, workouts
from ..storage import PhotoStorage, get_storage

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("", response_model=CheckinOut, status_code=status.HTTP_201_CREATED)
def create_workout(
    data: WorkoutIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(app_settings),
    today: dt.date = Depends(get_today),
    storage: PhotoStorage = Depends(get_storage),
):
    """Register a workout for today or yesterday. Points are computed here and stored."""
    return workouts.create_checkin(db, user, data, today, settings, storage)


@router.get("", response_model=list[WorkoutOut])
def list_workouts(
    person: Person = Query("all", description="all, me (você) ou opponent (sua dupla)"),
    period: Period = Query("week", description="week (semana atual), month (mês atual) ou all"),
    limit: int | None = Query(None, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
    storage: PhotoStorage = Depends(get_storage),
):
    """Workouts of both players, newest first (photos come as short-lived signed URLs)."""
    return workouts.list_workouts(db, user, person, period, today, limit, storage)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
    storage: PhotoStorage = Depends(get_storage),
):
    """Delete one of your own workouts from today or yesterday (its points are removed with it)."""
    workouts.delete_workout(db, user, workout_id, today, storage)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{workout_id}/photo", response_model=CheckinOut)
async def upload_photo(
    workout_id: int,
    photo: UploadFile = File(description="Imagem (até 8 MB); o servidor remove os metadados"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
    storage: PhotoStorage = Depends(get_storage),
):
    """Attach the proof photo to your workout of today or yesterday; the photo bonus is applied."""
    data = await photo.read(photos.MAX_UPLOAD_BYTES + 1)
    return photos.attach_photo(db, user, workout_id, data, today, storage)


@router.post("/{workout_id}/cheer", status_code=status.HTTP_204_NO_CONTENT)
def cheer(workout_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send "parabéns" for a workout of your duo (they get a notification)."""
    photos.cheer(db, user, workout_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
