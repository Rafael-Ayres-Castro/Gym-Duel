"""Unit tests for the pure rules in app.scoring."""

import datetime as dt

import pytest

from app.scoring import (
    WeekStats,
    calc_points,
    checkin_feedback,
    duel_message,
    leader,
    pct,
    streak,
    week_bounds,
)

ME, OPP = 1, 2


def stats(user_id: int, done: int, goal: int, points: int) -> WeekStats:
    return WeekStats(user_id=user_id, done=done, goal=goal, points=points)


# ---- calc_points ----


@pytest.mark.parametrize(
    ("minutes", "intensity", "expected"),
    [
        (30, "Moderada", 10),  # example from the spec
        (45, "Alta", 20),  # example from the spec
        (45, "Moderada", 15),
        (60, "Alta", 25),
        (30, "Leve", 5),
        (90, "Leve", 25),
        (31, "Moderada", 10),  # 10.33 rounds down
        (32, "Moderada", 11),  # 10.67 rounds up
        (5, "Leve", 5),  # never below the 5 point floor
        (300, "Alta", 105),
    ],
)
def test_calc_points(minutes, intensity, expected):
    assert calc_points(minutes, intensity) == expected


# ---- week_bounds / week turnover ----


def test_week_runs_monday_to_sunday():
    thursday = dt.date(2026, 10, 15)
    assert week_bounds(thursday) == (dt.date(2026, 10, 12), dt.date(2026, 10, 18))


def test_week_turnover_between_sunday_and_monday():
    sunday, monday = dt.date(2026, 10, 18), dt.date(2026, 10, 19)
    assert week_bounds(sunday)[0] == dt.date(2026, 10, 12)
    assert week_bounds(monday)[0] == monday


def test_week_across_months():
    assert week_bounds(dt.date(2026, 10, 1)) == (dt.date(2026, 9, 28), dt.date(2026, 10, 4))


# ---- pct ----


@pytest.mark.parametrize(
    ("done", "goal", "expected"),
    [(0, 4, 0), (3, 4, 75), (3, 3, 100), (2, 3, 67), (1, 3, 33), (5, 4, 100), (1, 7, 14), (1, 2, 50)],
)
def test_pct(done, goal, expected):
    assert pct(done, goal) == expected


# ---- leader ----


def test_leader_is_higher_pct_even_with_fewer_points():
    assert leader(stats(ME, 3, 4, 90), stats(OPP, 3, 3, 30)) == OPP


def test_leader_tie_on_pct_goes_to_more_points():
    assert leader(stats(ME, 4, 4, 60), stats(OPP, 3, 3, 55)) == ME
    assert leader(stats(ME, 3, 3, 40), stats(OPP, 4, 4, 55)) == OPP


def test_no_leader_when_nobody_trained():
    assert leader(stats(ME, 0, 4, 0), stats(OPP, 0, 3, 0)) is None


def test_no_leader_on_full_tie():
    assert leader(stats(ME, 2, 4, 30), stats(OPP, 2, 4, 30)) is None


def test_no_leader_without_opponent():
    assert leader(stats(ME, 3, 4, 45), None) is None


# ---- streak ----


def test_streak_counts_consecutive_closed_weeks():
    assert streak([True, True, False, True], current_week_met=False) == 2


def test_streak_adds_current_week_once_met():
    assert streak([True, True], current_week_met=True) == 3


def test_streak_current_week_unmet_does_not_break_it():
    assert streak([True], current_week_met=False) == 1


def test_streak_broken_last_week():
    assert streak([False, True, True], current_week_met=True) == 1


def test_streak_empty_history():
    assert streak([], current_week_met=False) == 0


# ---- duel_message (texts from the prototype) ----


def test_message_empty_week():
    msg = duel_message(stats(ME, 0, 4, 0), stats(OPP, 0, 3, 0), "Ana")
    assert msg == "Placar zerado. Quem treinar primeiro abre a semana na frente."


def test_message_opponent_hit_goal():
    msg = duel_message(stats(ME, 3, 4, 45), stats(OPP, 3, 3, 55), "Ana")
    assert msg == "Ana bateu a meta. Mais 1 treino e você empata."


def test_message_opponent_ahead_needs_plural():
    msg = duel_message(stats(ME, 1, 4, 15), stats(OPP, 2, 3, 30), "Ana")
    assert msg == "Ana está na frente. Mais 2 treinos e você empata."


def test_message_tie_on_goal_opponent_leads_on_points():
    msg = duel_message(stats(ME, 3, 3, 40), stats(OPP, 3, 3, 55), "Ana")
    assert msg == "Empate na meta. Ana lidera nos pontos por 15."


def test_message_tie_on_goal_me_leads_on_points():
    msg = duel_message(stats(ME, 4, 4, 60), stats(OPP, 3, 3, 55), "Ana")
    assert msg == "Empate na meta. Você lidera nos pontos por 5."


def test_message_me_ahead():
    assert duel_message(stats(ME, 3, 4, 45), stats(OPP, 1, 3, 15), "Ana") == "Você está na frente com 75% da meta."
    assert duel_message(stats(ME, 4, 4, 60), stats(OPP, 1, 3, 15), "Ana") == "Você bateu a meta e está na frente. Boa!"


def test_message_full_tie():
    assert duel_message(stats(ME, 2, 4, 30), stats(OPP, 2, 4, 30), "Ana") == "Empate total. O próximo treino desempata."


def test_message_waiting_for_opponent():
    assert duel_message(stats(ME, 1, 4, 15), None, "") == "O duelo começa assim que sua dupla se cadastrar."


# ---- checkin_feedback ----


def test_feedback_passing_the_opponent_and_hitting_goal():
    feedback = checkin_feedback(
        me_before=stats(ME, 3, 4, 45),
        me_after=stats(ME, 4, 4, 60),
        opponent=stats(OPP, 3, 3, 55),
        counts_for_current_week=True,
        streak_after=3,
        opponent_name="Ana",
    )
    assert feedback.message == "Você passou na frente!"
    assert feedback.pill == "Meta batida · sequência de 3 semanas"


def test_feedback_still_ahead_and_missing_workouts():
    feedback = checkin_feedback(stats(ME, 1, 4, 15), stats(ME, 2, 4, 30), stats(OPP, 0, 3, 0), True, 0, "Ana")
    assert feedback.message == "Você segue na frente!"
    assert feedback.pill == "Faltam 2 treinos para sua meta"


def test_feedback_tie_and_single_missing_workout():
    feedback = checkin_feedback(stats(ME, 1, 3, 15), stats(ME, 2, 3, 30), stats(OPP, 2, 3, 30), True, 0, "Ana")
    assert feedback.message == "Empate no placar!"
    assert feedback.pill == "Falta 1 treino para sua meta"


def test_feedback_closer_to_opponent():
    feedback = checkin_feedback(stats(ME, 0, 4, 0), stats(ME, 1, 4, 15), stats(OPP, 3, 3, 55), True, 0, "Ana")
    assert feedback.message == "Você está mais perto de Ana!"


def test_feedback_extra_workout_after_goal():
    feedback = checkin_feedback(stats(ME, 4, 4, 60), stats(ME, 5, 4, 75), stats(OPP, 1, 3, 15), True, 1, "Ana")
    assert feedback.pill == "Treino extra · pontos contam no desempate"


def test_feedback_singular_streak():
    feedback = checkin_feedback(stats(ME, 0, 1, 0), stats(ME, 1, 1, 15), stats(OPP, 0, 3, 0), True, 1, "Ana")
    assert feedback.pill == "Meta batida · sequência de 1 semana"


def test_feedback_workout_from_last_week():
    feedback = checkin_feedback(stats(ME, 0, 4, 0), stats(ME, 0, 4, 0), stats(OPP, 0, 3, 0), False, 0, "Ana")
    assert feedback.message == "Registrado na semana anterior."
    assert feedback.pill == "Não conta para o placar desta semana"


# ---- configurable rules ----

from app.scoring import DEFAULT_RULES, Rules, badges_reached, next_badge, streak_record, validate_rules  # noqa: E402


@pytest.mark.parametrize(
    ("minutes", "intensity", "photo", "rules", "expected"),
    [
        (45, "Moderada", True, DEFAULT_RULES, 20),  # the prototype example: 15 + 5 photo
        (45, "Moderada", False, Rules(minutes_per_point=2), 23),  # 22.5 rounds up
        (60, "Alta", False, Rules(minutes_per_point=4, intensity_adjust=10), 25),
        (60, "Leve", False, Rules(intensity_adjust=10), 10),
        (30, "Alta", True, Rules(intensity_adjust=0, photo_bonus=10), 20),
        (5, "Leve", False, Rules(intensity_adjust=10), 5),  # floor of 5 points
        (30, "Moderada", True, Rules(photo_bonus=0), 10),
    ],
)
def test_calc_points_with_rules(minutes, intensity, photo, rules, expected):
    assert calc_points(minutes, intensity, photo, rules) == expected


def test_validate_rules_accepts_only_the_listed_options():
    values = {"minutes_per_point": 2, "intensity_adjust": 10, "photo_bonus": 3, "week_winner_bonus": 0}
    assert validate_rules(values) == Rules(**values)
    with pytest.raises(ValueError):
        validate_rules({**values, "minutes_per_point": 5})
    with pytest.raises(ValueError):
        validate_rules({**values, "week_winner_bonus": 15})


def test_streak_record_is_the_longest_run():
    assert streak_record([True, True, False, True, True, True, False]) == 3
    assert streak_record([]) == 0


def test_badges_are_earned_once():
    assert badges_reached(2, set()) == [(2, 10)]
    assert badges_reached(4, {2}) == [(4, 20)]
    assert badges_reached(4, {2, 4}) == []
    assert badges_reached(1, set()) == []


def test_next_badge():
    assert next_badge(0, set()) == (2, 2)
    assert next_badge(3, {2}) == (4, 1)
    assert next_badge(1, {2}) == (4, 3)  # 2-week badge already earned in an older streak
    assert next_badge(12, {2, 4, 8, 12}) is None


# ---- week closing date ----

from app.services.weeks import last_closable_week  # noqa: E402


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (dt.date(2026, 10, 19), dt.date(2026, 10, 5)),  # Monday: Sunday is still "ontem", last week stays open
        (dt.date(2026, 10, 20), dt.date(2026, 10, 12)),  # Tuesday: last week closes
        (dt.date(2026, 10, 25), dt.date(2026, 10, 12)),  # Sunday
    ],
)
def test_last_closable_week(today, expected):
    assert last_closable_week(today) == expected
