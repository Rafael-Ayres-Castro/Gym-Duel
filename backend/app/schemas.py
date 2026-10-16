"""Request and response bodies of the API (documented automatically at /docs)."""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator, model_validator

from .scoring import MAX_DURATION_MIN, MAX_WEEKLY_GOAL, MIN_DURATION_MIN, MIN_WEEKLY_GOAL, validate_rules

WorkoutType = Literal["Musculação", "Corrida", "Funcional", "Aula", "Outro"]
Intensity = Literal["Leve", "Moderada", "Alta"]
PlayerColor = Literal["blue", "pink"]
Person = Literal["all", "me", "opponent"]
Period = Literal["week", "month", "all"]

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
WeeklyGoal = Annotated[int, Field(ge=MIN_WEEKLY_GOAL, le=MAX_WEEKLY_GOAL, description="Treinos por semana (1 a 7)")]
Note = Annotated[str, StringConstraints(strip_whitespace=True, max_length=140)]


def _fits_bcrypt(value: str) -> str:
    # bcrypt only looks at the first 72 bytes; refuse longer instead of silently truncating.
    if len(value.encode()) > 72:
        raise ValueError("A senha pode ter no máximo 72 bytes.")
    return value


Password = Annotated[str, Field(min_length=6, max_length=72), AfterValidator(_fits_bcrypt)]


# ---- Auth and profile ----


class RegisterIn(BaseModel):
    name: Name
    email: EmailStr
    password: Password
    weekly_goal: WeeklyGoal


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    first_name: str
    email: str
    weekly_goal: int = Field(description="Meta em vigor nesta semana")
    next_weekly_goal: int | None = Field(description="Meta agendada para a próxima semana, se mudou")
    balance: int = Field(description="Saldo de pontos (treinos + bônus − resgates)")
    color: PlayerColor
    created_at: dt.datetime


class AuthOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class MeUpdate(BaseModel):
    name: Name | None = None
    weekly_goal: WeeklyGoal | None = Field(default=None, description="Vale a partir da próxima semana")


class EmailChangeIn(BaseModel):
    email: EmailStr
    current_password: str = Field(description="Senha atual, para confirmar que é você")


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: Password


class ProfileStatsOut(BaseModel):
    """All-time numbers of the logged user, for the account screen."""

    workouts: int
    minutes: int
    favorite_type: str | None = Field(description="Modalidade mais registrada; None sem treinos")
    points_earned: int = Field(description="Tudo o que já entrou no saldo: treinos e bônus")
    points_spent: int = Field(description="Gasto em prêmios resgatados")
    weeks_closed: int = Field(description="Semanas encerradas desde o cadastro")
    weeks_won: int
    weeks_goal_met: int
    streak: int
    record: int
    badges: int
    challenges_won: int
    rewards_redeemed: int


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
    has_photo: bool
    photo_url: str | None = Field(description="URL assinada da foto, válida por poucos minutos")
    created_at: dt.datetime


# ---- Rules ----


class RulesValues(BaseModel):
    minutes_per_point: int = Field(description="1 ponto a cada X minutos (2, 3 ou 4)")
    intensity_adjust: int = Field(description="Leve tira e alta soma este valor (0, 5 ou 10)")
    photo_bonus: int = Field(description="Bônus por treino com foto (0, 3, 5 ou 10)")
    week_winner_bonus: int = Field(description="Bônus de saldo para quem vence a semana (0, 10, 20 ou 30)")


class RuleProposalIn(RulesValues):
    @model_validator(mode="after")
    def allowed_values(self) -> RuleProposalIn:
        try:
            validate_rules(self.model_dump())
        except ValueError as error:
            raise ValueError(f"Valor fora das opções permitidas: {error}") from None
        return self


class RuleProposalOut(BaseModel):
    id: int
    proposed_by_me: bool
    proposed_by_name: str
    values: RulesValues
    created_at: dt.datetime


class RulesStateOut(BaseModel):
    current: RulesValues
    options: dict[str, list[int]]
    pending: RuleProposalOut | None


# ---- Streaks ----


class StreakWeekOut(BaseModel):
    week_start: dt.date
    is_current: bool
    goal: int | None = Field(description="Meta daquela semana; None antes do cadastro")
    done: int
    met: bool


class BadgeOut(BaseModel):
    milestone: int
    bonus: int
    earned: bool


class NextBadgeOut(BaseModel):
    milestone: int
    weeks_left: int


class PlayerStreaksOut(BaseModel):
    user_id: int
    name: str
    color: PlayerColor
    is_me: bool
    streak: int
    record: int
    weeks: list[StreakWeekOut]
    badges: list[BadgeOut]
    next_badge: NextBadgeOut | None


class StreaksOut(BaseModel):
    players: list[PlayerStreaksOut]


# ---- Notifications ----


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    message: str
    payload: dict | None
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
    rules: RulesValues = Field(description="Regras de pontos em vigor nesta semana")


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


# ---- Rewards ----

RewardTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class RewardIn(BaseModel):
    title: RewardTitle
    cost: int = Field(description="50, 100, 150, 200 ou 300 pts")


class RewardOut(BaseModel):
    id: int
    title: str
    cost: int
    created_by: int


class StoreOut(BaseModel):
    balance: int
    opponent_balance: int | None
    opponent_name: str | None
    offered_to_me: list[RewardOut] = Field(description="Oferecidos pela dupla: você resgata")
    offered_by_me: list[RewardOut] = Field(description="Oferecidos por você: a dupla resgata")
    costs: list[int]


class RedemptionOut(BaseModel):
    id: int
    title: str
    cost: int
    status: Literal["pending", "fulfilled", "received"]
    created_at: dt.datetime
    redeemed_on: dt.date = Field(description="Dia do resgate no fuso do casal")
    owner_name: str
    owner_color: PlayerColor
    redeemer_name: str
    redeemer_color: PlayerColor


class RedeemOut(BaseModel):
    redemption_id: int
    balance: int


class BadgesOut(BaseModel):
    challenges: int = Field(description="Desafios recebidos esperando sua resposta")
    rewards: int = Field(description="Resgates da dupla que você ainda precisa cumprir")


# ---- Challenges ----

StakeText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]


class ChallengeIn(BaseModel):
    kind: Literal["count", "minutes", "goal"] = Field(description="Mais treinos, mais minutos ou primeiro a bater a meta")
    workout_type: WorkoutType | None = Field(default=None, description="Só conta este tipo de treino (opcional)")
    period: Literal["week", "weekend"] = Field(description="Esta semana (seg a dom) ou fim de semana (sáb e dom)")
    stake_points: int | None = Field(default=None, description="Bônus para quem vencer: 10, 20 ou 50")
    stake_text: StakeText | None = Field(default=None, description="Combinado em texto livre, no lugar dos pontos")

    @model_validator(mode="after")
    def consistent(self) -> ChallengeIn:
        if self.stake_text == "":
            self.stake_text = None
        if (self.stake_points is None) == (self.stake_text is None):
            raise ValueError("Escolha pontos ou escreva o combinado.")
        if self.stake_points is not None and self.stake_points not in (10, 20, 50):
            raise ValueError("A aposta em pontos é 10, 20 ou 50.")
        if self.kind == "goal" and (self.period != "week" or self.workout_type is not None):
            raise ValueError("Primeiro a bater a meta vale só para a semana inteira, sem tipo de treino.")
        return self


class ChallengePlayerOut(BaseModel):
    user_id: int
    name: str
    color: PlayerColor
    is_me: bool
    value: int = Field(description="Treinos, minutos ou % da meta, conforme o modelo")


class ChallengeOut(BaseModel):
    id: int
    title: str
    base_title: str
    kind: Literal["count", "minutes", "goal"]
    workout_type: str | None
    period: Literal["week", "weekend"]
    starts_on: dt.date
    ends_on: dt.date
    stake_points: int | None
    stake_text: str | None
    status: Literal["pending", "active", "done"]
    created_by_me: bool
    created_by_name: str
    players: list[ChallengePlayerOut] = Field(description="Você primeiro")
    leader_id: int | None
    first_to_goal_id: int | None
    winner_id: int | None
    winner_name: str | None
    winner_color: PlayerColor | None


class ChallengeBoardOut(BaseModel):
    incoming: list[ChallengeOut] = Field(description="Desafios que você recebeu e ainda não respondeu")
    outgoing: list[ChallengeOut] = Field(description="Desafios que você enviou, aguardando aceite")
    active: list[ChallengeOut]
    done: list[ChallengeOut] = Field(description="Os 10 concluídos mais recentes")
