"""Weekly scoreboard and period totals for the history header."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..clock import get_today
from ..db import get_db
from ..models import User
from ..schemas import Period, ScoreboardOut, SummaryOut
from ..security import get_current_user
from ..services import stats

router = APIRouter(tags=["scoreboard"])


@router.get("/scoreboard", response_model=ScoreboardOut)
def scoreboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
):
    """This week's duel: % of goal, points, streak, leader, message and training days."""
    return stats.build_scoreboard(db, stats.load_duel(db, user, today))


@router.get("/summary", response_model=SummaryOut)
def summary(
    period: Period = Query("week"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
):
    """Workouts and points of each player in the period (history header)."""
    return stats.build_summary(db, stats.load_duel(db, user, today), period)
