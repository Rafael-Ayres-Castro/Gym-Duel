"""The logged user's own profile, credentials and all-time stats."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..clock import get_today
from ..db import get_db
from ..models import User
from ..schemas import EmailChangeIn, MeUpdate, PasswordChangeIn, ProfileStatsOut, UserOut
from ..security import get_current_user
from ..services import account, players, profile

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserOut)
def read_me(user: User = Depends(get_current_user), db: Session = Depends(get_db), today: dt.date = Depends(get_today)):
    return players.user_out(db, user, today)


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
        # Takes effect next Monday, so the scoreboard of the week in course never moves.
        players.schedule_goal(db, user.id, data.weekly_goal, today)
    db.commit()
    return players.user_out(db, user, today)


@router.put("/email", response_model=UserOut)
def change_email(
    data: EmailChangeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
):
    """Change the login e-mail. Asks for the current password."""
    account.change_email(db, user, data.email, data.current_password)
    return players.user_out(db, user, today)


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(data: PasswordChangeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Change the password. Asks for the current one; this session stays logged in."""
    account.change_password(db, user, data.current_password, data.new_password)


@router.get("/stats", response_model=ProfileStatsOut)
def read_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db), today: dt.date = Depends(get_today)):
    """All-time numbers for the account screen: workouts, points, weeks won, streaks..."""
    return profile.build_profile_stats(db, user, today)
