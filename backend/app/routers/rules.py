"""The game rules as data, so the "Regras" screen always shows the values actually in force."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import scoring
from ..config import Settings, app_settings
from ..models import User
from ..schemas import RulesOut
from ..security import get_current_user

router = APIRouter(tags=["rules"])

# Workouts used to illustrate the formula on the rules screen.
EXAMPLES = ((30, "Moderada"), (45, "Alta"), (60, "Leve"), (15, "Leve"))


@router.get("/rules", response_model=RulesOut)
def rules(_: User = Depends(get_current_user), settings: Settings = Depends(app_settings)):
    """Scoring and check-in rules, including the examples computed by the real formula."""
    return {
        "minutes_per_point": scoring.MINUTES_PER_POINT,
        "min_points": scoring.MIN_POINTS,
        "intensity_adjustment": scoring.INTENSITY_ADJUSTMENT,
        "min_duration_min": scoring.MIN_DURATION_MIN,
        "max_duration_min": scoring.MAX_DURATION_MIN,
        "min_weekly_goal": scoring.MIN_WEEKLY_GOAL,
        "max_weekly_goal": scoring.MAX_WEEKLY_GOAL,
        "max_workouts_per_day": settings.max_workouts_per_day,
        "examples": [
            {"duration_min": minutes, "intensity": intensity, "points": scoring.calc_points(minutes, intensity)}
            for minutes, intensity in EXAMPLES
        ],
    }
