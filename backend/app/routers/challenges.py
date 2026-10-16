"""Challenges between the two members."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..clock import get_today
from ..db import get_db
from ..models import User
from ..schemas import ChallengeBoardOut, ChallengeIn
from ..security import get_current_user
from ..services import challenges

router = APIRouter(prefix="/challenges", tags=["challenges"])
NO_CONTENT = status.HTTP_204_NO_CONTENT


@router.get("", response_model=ChallengeBoardOut)
def read_challenges(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Received, sent, active (with live progress from the workouts) and recently finished."""
    return challenges.board(db, user)


@router.post("", response_model=ChallengeBoardOut, status_code=status.HTTP_201_CREATED)
def create_challenge(
    data: ChallengeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
):
    """Challenge your duo; it only counts after they accept."""
    challenges.create(db, user, data, today)
    return challenges.board(db, user)


@router.post("/{challenge_id}/accept", status_code=NO_CONTENT)
def accept(challenge_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    challenges.accept(db, user, challenge_id)
    return Response(status_code=NO_CONTENT)


@router.post("/{challenge_id}/decline", status_code=NO_CONTENT)
def decline(challenge_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Turn the challenge down (it is removed and the author is told)."""
    challenges.decline(db, user, challenge_id)
    return Response(status_code=NO_CONTENT)


@router.delete("/{challenge_id}", status_code=NO_CONTENT)
def cancel(challenge_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Withdraw a challenge you sent that was not accepted yet."""
    challenges.cancel(db, user, challenge_id)
    return Response(status_code=NO_CONTENT)
