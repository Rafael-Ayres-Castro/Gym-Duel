"""Pure business rules of Gym Duel: points, weeks, goal %, leader, streak and messages.

Nothing here touches the database or the clock, so every rule can be unit tested
with plain values. The frontend mirrors `calc_points` only to preview points;
the backend result is always the one stored.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

INTENSITY_ADJUSTMENT = {"Leve": -5, "Moderada": 0, "Alta": 5}
WORKOUT_TYPES = ("Musculação", "Corrida", "Funcional", "Aula", "Outro")
MIN_POINTS = 5
MINUTES_PER_POINT = 3
MIN_DURATION_MIN = 5
MAX_DURATION_MIN = 300
MIN_WEEKLY_GOAL = 1
MAX_WEEKLY_GOAL = 7


def _round_half_up(numerator: int, denominator: int) -> int:
    """Integer division rounded half up, matching JavaScript's Math.round for positives.

    Python's round() uses banker's rounding, which would make backend and
    frontend disagree on .5 cases.
    """
    return (2 * numerator + denominator) // (2 * denominator)


def calc_points(duration_min: int, intensity: str) -> int:
    """Points for one workout: 1 point per 3 minutes plus the intensity adjustment, minimum 5."""
    return max(MIN_POINTS, _round_half_up(duration_min, MINUTES_PER_POINT) + INTENSITY_ADJUSTMENT[intensity])


def week_bounds(day: date) -> tuple[date, date]:
    """Monday and Sunday of the week that contains `day`."""
    start = day - timedelta(days=day.weekday())
    return start, start + timedelta(days=6)


def pct(done: int, goal: int) -> int:
    """Share of the weekly goal completed, rounded and capped at 100."""
    return min(100, _round_half_up(100 * done, goal))


def first_name(name: str) -> str:
    parts = name.split()
    return parts[0] if parts else name


@dataclass(frozen=True)
class WeekStats:
    """One player's numbers for a single week."""

    user_id: int
    done: int
    goal: int
    points: int

    @property
    def pct(self) -> int:
        return pct(self.done, self.goal)

    @property
    def goal_met(self) -> bool:
        return self.done >= self.goal


def leader(me: WeekStats, opponent: WeekStats | None) -> int | None:
    """User id of the week leader: higher %, then more points. None if nobody trained or full tie."""
    if opponent is None or (me.done == 0 and opponent.done == 0):
        return None
    if me.pct != opponent.pct:
        return me.user_id if me.pct > opponent.pct else opponent.user_id
    if me.points != opponent.points:
        return me.user_id if me.points > opponent.points else opponent.user_id
    return None


def streak(closed_weeks_met: Iterable[bool], current_week_met: bool) -> int:
    """Consecutive closed weeks with the goal met (most recent first), plus 1 if this week is met.

    The current week never breaks the streak: it only adds once the goal is reached.
    """
    count = 0
    for met in closed_weeks_met:
        if not met:
            break
        count += 1
    return count + (1 if current_week_met else 0)


def _plural(count: int, singular: str, plural: str) -> str:
    return singular if count == 1 else plural


def duel_message(me: WeekStats, opponent: WeekStats | None, opponent_name: str) -> str:
    """Scoreboard message, always written from the logged user's point of view."""
    if opponent is None:
        return "O duelo começa assim que sua dupla se cadastrar."
    if me.done == 0 and opponent.done == 0:
        return "Placar zerado. Quem treinar primeiro abre a semana na frente."

    lead = leader(me, opponent)
    if lead == opponent.user_id:
        if me.pct == opponent.pct:
            return f"Empate na meta. {opponent_name} lidera nos pontos por {opponent.points - me.points}."
        # Workouts the user needs to reach the opponent's % (ceil without floats).
        need = max(1, -(-opponent.pct * me.goal // 100) - me.done)
        lead_text = f"{opponent_name} bateu a meta." if opponent.pct == 100 else f"{opponent_name} está na frente."
        return f"{lead_text} Mais {need} {_plural(need, 'treino', 'treinos')} e você empata."
    if lead == me.user_id:
        if me.pct == opponent.pct:
            return f"Empate na meta. Você lidera nos pontos por {me.points - opponent.points}."
        if me.pct == 100:
            return "Você bateu a meta e está na frente. Boa!"
        return f"Você está na frente com {me.pct}% da meta."
    return "Empate total. O próximo treino desempata."


@dataclass(frozen=True)
class CheckinFeedback:
    message: str
    pill: str


def checkin_feedback(
    me_before: WeekStats,
    me_after: WeekStats,
    opponent: WeekStats | None,
    counts_for_current_week: bool,
    streak_after: int,
    opponent_name: str,
) -> CheckinFeedback:
    """Headline and pill shown on the success screen right after a check-in."""
    if not counts_for_current_week:
        return CheckinFeedback("Registrado na semana anterior.", "Não conta para o placar desta semana")

    lead_before = leader(me_before, opponent)
    lead_after = leader(me_after, opponent)
    if opponent is None:
        message = "Treino registrado!"
    elif lead_after == me_after.user_id and lead_before != me_after.user_id:
        message = "Você passou na frente!"
    elif lead_after == me_after.user_id:
        message = "Você segue na frente!"
    elif lead_after is None:
        message = "Empate no placar!"
    else:
        message = f"Você está mais perto de {opponent_name}!"

    if not me_before.goal_met and me_after.goal_met:
        pill = f"Meta batida · sequência de {streak_after} {_plural(streak_after, 'semana', 'semanas')}"
    elif not me_after.goal_met:
        missing = me_after.goal - me_after.done
        verb = _plural(missing, "Falta", "Faltam")
        pill = f"{verb} {missing} {_plural(missing, 'treino', 'treinos')} para sua meta"
    else:
        pill = "Treino extra · pontos contam no desempate"
    return CheckinFeedback(message, pill)
