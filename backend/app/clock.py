"""Single source of "today" for the whole app, in São Paulo time.

Routes depend on `get_today` instead of calling the clock directly, so tests
can override it to simulate any day (including week turnovers).
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import Depends

from .config import TIMEZONE, Settings, app_settings


def today_in_sao_paulo(settings: Settings) -> date:
    if settings.app_today is not None:
        return settings.app_today
    return datetime.now(ZoneInfo(TIMEZONE)).date()


def get_today(settings: Settings = Depends(app_settings)) -> date:
    return today_in_sao_paulo(settings)
