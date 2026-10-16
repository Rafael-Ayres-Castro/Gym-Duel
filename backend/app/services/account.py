"""Account credentials: e-mail uniqueness and changing the e-mail or the password.

Both changes ask for the current password, so a phone left unlocked with the app open
is not enough to take over the account.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import api_error
from ..models import User
from ..security import hash_password, verify_password


def normalize_email(email: str) -> str:
    return email.strip().lower()


def ensure_email_free(db: Session, email: str, owner: User | None = None) -> None:
    """Raise 409 if another account already uses `email` (the owner may keep their own)."""
    taken_by = db.scalar(select(User).where(User.email == email))
    if taken_by is not None and taken_by is not owner:
        raise api_error(409, "email_taken", "Já existe uma conta com este e-mail.")


def _confirm_password(user: User, password: str) -> None:
    # 403, not 401: the session is valid, only the confirmation failed (401 would log the user out).
    if not verify_password(password, user.password_hash):
        raise api_error(403, "wrong_password", "Senha atual incorreta. Confira e tente de novo.")


def change_email(db: Session, user: User, email: str, current_password: str) -> None:
    _confirm_password(user, current_password)
    email = normalize_email(email)
    ensure_email_free(db, email, owner=user)
    user.email = email
    db.commit()


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    _confirm_password(user, current_password)
    if verify_password(new_password, user.password_hash):
        raise api_error(422, "same_password", "A nova senha precisa ser diferente da atual.")
    user.password_hash = hash_password(new_password)
    db.commit()
