"""The logged user's own profile."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..clock import get_today
from ..db import get_db
from ..models import User
from ..schemas import MeUpdate, UserOut
from ..scoring import week_bounds
from ..security import get_current_user
from ..services import players

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserOut)
def read_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return players.user_out(db, user)


@router.patch("", response_model=UserOut)
def update_me(
    data: MeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
):
    if data.name is not None:
        user.name = data.name
    if data.weekly_goal is not None:
        # Applies from this week on; closed weeks keep the goal they were played with.
        players.set_goal(db, user.id, data.weekly_goal, week_bounds(today)[0])
    db.commit()
    return players.user_out(db, user)
