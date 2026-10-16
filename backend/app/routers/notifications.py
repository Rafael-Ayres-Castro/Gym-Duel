"""Unread notifications (shown as toasts) and marking them as read."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import NotificationOut
from ..security import get_current_user
from ..services import notifications

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def unread(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return notifications.unread(db, user.id)


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications.mark_all_read(db, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
