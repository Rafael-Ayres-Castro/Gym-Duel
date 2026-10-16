"""Counters shown as pink pills on the navigation (Desafios, Prêmios)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import BadgesOut
from ..security import get_current_user
from ..services import rewards

router = APIRouter(tags=["badges"])


@router.get("/badges", response_model=BadgesOut)
def badges(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"challenges": 0, "rewards": rewards.pending_to_fulfill(db, user)}
