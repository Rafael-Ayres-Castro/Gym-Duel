"""Request and response bodies of the API (documented automatically at /docs)."""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from .scoring import MAX_DURATION_MIN, MAX_WEEKLY_GOAL, MIN_DURATION_MIN, MIN_WEEKLY_GOAL

WorkoutType = Literal["Musculação", "Corrida", "Funcional", "Aula", "Outro"]
Intensity = Literal["Leve", "Moderada", "Alta"]
PlayerColor = Literal["blue", "pink"]
Person = Literal["all", "me", "opponent"]
Period = Literal["week", "month", "all"]

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
WeeklyGoal = Annotated[int, Field(ge=MIN_WEEKLY_GOAL, le=MAX_WEEKLY_GOAL, description="Treinos por semana (1 a 7)")]
Note = Annotated[str, StringConstraints(strip_whitespace=True, max_length=140)]


# ---- Auth and profile ----


class RegisterIn(BaseModel):
    name: Name
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    weekly_goal: WeeklyGoal

    @field_validator("password")
    @classmethod
    def fits_bcrypt(cls, value: str) -> str:
        # bcrypt only looks at the first 72 bytes; refuse longer instead of silently truncating.
        if len(value.encode()) > 72:
            raise ValueError("A senha pode ter no máximo 72 bytes.")
        return value


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    first_name: str
    email: str
    weekly_goal: int
    color: PlayerColor
    created_at: dt.datetime


class AuthOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class MeUpdate(BaseModel):
    name: Name | None = None
    weekly_goal: WeeklyGoal | None = Field(default=None, description="Vale da semana atual em diante")


# ---- Workouts ----


class WorkoutIn(BaseModel):
    type: WorkoutType
    duration_min: int = Field(ge=MIN_DURATION_MIN, le=MAX_DURATION_MIN)
    intensity: Intensity
    date: dt.date = Field(description="Hoje ou ontem, no fuso de São Paulo")
    note: Note = ""


class WorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str
    color: PlayerColor
    date: dt.date
    type: str
    duration_min: int
    intensity: str
    points: int
    note: str
    created_at: dt.datetime


# ---- Scoreboard ----


class PlayerOut(BaseModel):
    user_id: int
    name: str
    color: PlayerColor
    is_me: bool
    done: int
    goal: int
    pct: int
    points: int
    streak: int
    is_leader: bool
    days: list[bool] = Field(description="Treinou em cada dia da semana, de segunda a domingo")


class ScoreboardOut(BaseModel):
    today: dt.date
    week_start: dt.date
    week_end: dt.date
    players: list[PlayerOut] = Field(description="Você primeiro, depois sua dupla (se já cadastrada)")
    leader_id: int | None
    duel_message: str
    waiting_for_opponent: bool


class FeedbackOut(BaseModel):
    message: str
    pill: str
    counts_for_current_week: bool


class CheckinOut(BaseModel):
    workout: WorkoutOut
    scoreboard: ScoreboardOut
    feedback: FeedbackOut


class SummaryPlayerOut(BaseModel):
    user_id: int
    name: str
    color: PlayerColor
    is_me: bool
    workouts: int
    points: int
    pct: int = Field(description="% da meta na semana atual")


class SummaryOut(BaseModel):
    period: Period
    start: dt.date | None
    end: dt.date
    players: list[SummaryPlayerOut]
