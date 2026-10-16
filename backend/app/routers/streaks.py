"""Streaks, records and badges of both players."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..clock import get_today
from ..db import get_db
from ..models import User
from ..schemas import StreaksOut
from ..security import get_current_user
from ..services import stats, streaks

router = APIRouter(tags=["streaks"])


@router.get("/streaks", response_model=StreaksOut)
def read_streaks(user: User = Depends(get_current_user), db: Session = Depends(get_db), today: dt.date = Depends(get_today)):
    """Current streak, record, the last 9 weeks and badges (2, 4, 8, 12 weeks) of each player."""
    return streaks.build_streaks(db, stats.load_duel(db, user, today))
