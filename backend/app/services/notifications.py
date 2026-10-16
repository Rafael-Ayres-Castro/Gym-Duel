"""Simple in-app notifications: stored per user and shown as toasts when they next open the app."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..models import Notification


def notify(db: Session, user_id: int, kind: str, message: str, payload: dict | None = None) -> None:
    db.add(Notification(user_id=user_id, kind=kind, message=message, payload=payload))


def unread(db: Session, user_id: int) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .order_by(Notification.created_at, Notification.id)
    )
    return list(db.scalars(stmt))


def mark_all_read(db: Session, user_id: int) -> None:
    db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=dt.datetime.now(dt.UTC))
    )
    db.commit()
