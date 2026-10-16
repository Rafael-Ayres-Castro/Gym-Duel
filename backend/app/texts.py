"""pt-BR labels used in server-generated messages (notifications), matching the frontend's format.js."""

from __future__ import annotations

import datetime as dt

MONTHS_SHORT = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def plural(count: int, singular: str, plural_form: str) -> str:
    return singular if count == 1 else plural_form


def day_month(day: dt.date) -> str:
    """'20 de out'"""
    return f"{day.day} de {MONTHS_SHORT[day.month - 1]}"


def week_range(week_start: dt.date) -> str:
    """'13 a 19 de out' or, across months, '29 de set a 5 de out'."""
    end = week_start + dt.timedelta(days=6)
    if week_start.month == end.month:
        return f"{week_start.day} a {day_month(end)}"
    return f"{day_month(week_start)} a {day_month(end)}"


def challenge_title(kind: str, workout_type: str | None, period: str | None = None) -> str:
    """'Mais treinos de musculação na semana', 'Mais minutos de treino no fim de semana', ..."""
    sport = workout_type.lower() if workout_type else None
    if kind == "count":
        base = "Mais treinos" + (f" de {sport}" if sport else "")
    elif kind == "minutes":
        base = "Mais minutos" + (f" de {sport}" if sport else " de treino")
    else:
        base = "Primeiro a bater a meta"
    suffix = {"week": " na semana", "weekend": " no fim de semana"}.get(period or "", "")
    return base + suffix
