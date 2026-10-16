"""Sign up and log in. The app holds at most MAX_USERS people (the couple)."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clock import get_today
from ..config import Settings, app_settings
from ..db import get_db
from ..errors import api_error
from ..models import User
from ..schemas import AuthOut, LoginIn, RegisterIn
from ..scoring import week_bounds
from ..security import create_access_token, hash_password, verify_password
from ..services import players

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_response(db: Session, user: User, settings: Settings, today: dt.date) -> dict:
    return {"access_token": create_access_token(user.id, settings), "user": players.user_out(db, user, today)}


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterIn,
    db: Session = Depends(get_db),
    settings: Settings = Depends(app_settings),
    today: dt.date = Depends(get_today),
):
    if players.count_users(db) >= settings.max_users:
        raise api_error(403, "registration_closed", "O cadastro está fechado: a dupla do Gym Duel já está completa.")
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise api_error(409, "email_taken", "Já existe uma conta com este e-mail.")

    user = User(name=data.name, email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.flush()
    players.set_goal(db, user.id, data.weekly_goal, week_bounds(today)[0])
    db.commit()
    return _auth_response(db, user, settings, today)


@router.post("/login", response_model=AuthOut)
def login(
    data: LoginIn,
    db: Session = Depends(get_db),
    settings: Settings = Depends(app_settings),
    today: dt.date = Depends(get_today),
):
    user = db.scalar(select(User).where(User.email == data.email.strip().lower()))
    if user is None:
        raise api_error(401, "unknown_email", "Não encontramos uma conta com este e-mail.")
    if not verify_password(data.password, user.password_hash):
        raise api_error(401, "wrong_password", "Senha incorreta. Confira e tente de novo.")
    return _auth_response(db, user, settings, today)
