"""Housekeeping that runs before every API request (cheap when there is nothing to do).

Replaces a scheduler: closes finished weeks and settles finished challenges.
"""

from __future__ import annotations

import datetime as dt

from fastapi import Depends
from sqlalchemy.orm import Session

from .clock import get_today
from .db import get_db
from .services import challenges, weeks


def run_maintenance(db: Session = Depends(get_db), today: dt.date = Depends(get_today)) -> None:
    weeks.close_finished_weeks(db, today)
    challenges.close_finished(db, today)
