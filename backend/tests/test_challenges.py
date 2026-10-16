"""Challenges: validation, accept/decline/cancel, progress derived from workouts and settlement."""

import datetime as dt

import pytest

from app.scoring import first_to_reach, goal_reached_at, higher_value_winner

MONDAY = dt.date(2026, 10, 12)


def day(offset: int) -> dt.date:
    return MONDAY + dt.timedelta(days=offset)


def challenge(player, **fields):
    body = {"kind": "count", "workout_type": None, "period": "week", "stake_points": 20, "stake_text": None, **fields}
    return player.post("/challenges", body)


def train(player, clock, offset: int, **checkin) -> None:
    clock.today = day(offset)
    assert player.checkin(**checkin).status_code == 201


@pytest.fixture
def duo(make_player, clock):
    clock.today = MONDAY
    return make_player("Rafael", "rafael@email.com", 2), make_player("Ana", "ana@email.com", 1)


# ---- pure rules ----


def test_higher_value_winner():
    assert higher_value_winner({1: 3, 2: 1}) == 1
    assert higher_value_winner({1: 0, 2: 120}) == 2
    assert higher_value_winner({1: 2, 2: 2}) is None
    assert higher_value_winner({1: 0, 2: 0}) is None


def test_goal_reached_at_and_first_to_reach():
    morning, night = dt.datetime(2026, 10, 14, 9), dt.datetime(2026, 10, 14, 21)
    rafael = goal_reached_at([(day(3), night), (day(1), morning)], goal=2)
    assert rafael == (day(3), night)
    assert goal_reached_at([(day(1), morning)], goal=2) is None
    ana = goal_reached_at([(day(2), morning)], goal=1)
    assert first_to_reach({1: rafael, 2: ana}) == 2
    assert first_to_reach({1: (day(2), morning), 2: (day(2), night)}) == 1  # same day: earlier check-in
    assert first_to_reach({1: None, 2: None}) is None


# ---- validation and flow ----


def test_validation(duo):
    rafael, _ = duo
    assert challenge(rafael, stake_points=None).status_code == 422  # no stake
    assert challenge(rafael, stake_text="jantar").status_code == 422  # both stakes
    assert challenge(rafael, stake_points=30).status_code == 422
    assert challenge(rafael, kind="goal", period="weekend").status_code == 422
    assert challenge(rafael, kind="goal", workout_type="Corrida").status_code == 422
    assert challenge(rafael, stake_points=None, stake_text="   ").status_code == 422


def test_needs_a_duo(make_player, clock):
    clock.today = MONDAY
    alone = make_player("Rafael", "rafael@email.com", 2)
    assert challenge(alone).json()["detail"]["code"] == "no_duo"


def test_create_accept_and_decline(duo):
    rafael, ana = duo
    board = challenge(rafael, workout_type="Musculação").json()
    sent = board["outgoing"][0]
    assert sent["title"] == "Mais treinos de musculação na semana"
    assert (sent["starts_on"], sent["ends_on"]) == ("2026-10-12", "2026-10-18")
    assert ana.notifications() == ["Rafael te desafiou: mais treinos de musculação na semana. Responda em Desafios."]
    assert ana.get("/badges").json()["challenges"] == 1
    assert ana.get("/challenges").json()["incoming"][0]["id"] == sent["id"]

    assert rafael.post(f"/challenges/{sent['id']}/accept").status_code == 403  # the author cannot accept
    assert ana.post(f"/challenges/{sent['id']}/accept").status_code == 204
    assert [c["id"] for c in rafael.get("/challenges").json()["active"]] == [sent["id"]]
    assert ana.get("/badges").json()["challenges"] == 0
    assert any("Ana aceitou o desafio" in message for message in rafael.notifications())

    second = challenge(rafael, kind="minutes").json()["outgoing"][0]
    assert ana.post(f"/challenges/{second['id']}/decline").status_code == 204
    assert rafael.get("/challenges").json()["outgoing"] == []
    assert any("Ana recusou o desafio" in message for message in rafael.notifications())


def test_only_the_author_cancels(duo):
    rafael, ana = duo
    sent = challenge(rafael).json()["outgoing"][0]
    assert ana.delete(f"/challenges/{sent['id']}").status_code == 403
    assert rafael.delete(f"/challenges/{sent['id']}").status_code == 204
    assert ana.get("/challenges").json()["incoming"] == []


# ---- progress ----


def accepted(rafael, ana, **fields) -> int:
    challenge_id = challenge(rafael, **fields).json()["outgoing"][0]["id"]
    assert ana.post(f"/challenges/{challenge_id}/accept").status_code == 204
    return challenge_id


def values(player) -> dict:
    active = player.get("/challenges").json()["active"][0]
    return {p["name"]: p["value"] for p in active["players"]} | {"leader": active["leader_id"]}


def test_progress_counts_only_the_type_and_the_period(duo, clock):
    rafael, ana = duo
    accepted(rafael, ana, workout_type="Musculação")
    train(rafael, clock, 0, type="Musculação")
    train(rafael, clock, 1, type="Corrida")  # other type: does not count
    train(ana, clock, 1, type="Musculação")
    train(rafael, clock, 2, type="Musculação")
    assert values(rafael) == {"Rafael": 2, "Ana": 1, "leader": rafael.id}


def test_minutes_on_the_weekend(duo, clock):
    rafael, ana = duo
    clock.today = day(4)  # Friday
    accepted(rafael, ana, kind="minutes", period="weekend", stake_points=None, stake_text="quem perder lava a louça")
    train(rafael, clock, 4, minutes=90)  # Friday: outside the weekend
    train(ana, clock, 5, minutes=45)
    train(rafael, clock, 6, minutes=30)
    assert values(ana) == {"Ana": 45, "Rafael": 30, "leader": ana.id}


def test_first_to_reach_the_goal_leads(duo, clock):
    rafael, ana = duo  # goals: Rafael 2, Ana 1
    accepted(rafael, ana, kind="goal")
    train(rafael, clock, 0)
    assert values(rafael) == {"Rafael": 50, "Ana": 0, "leader": rafael.id}
    train(ana, clock, 1)  # Ana hits 100% first
    train(rafael, clock, 2)  # Rafael only on Wednesday
    active = rafael.get("/challenges").json()["active"][0]
    assert active["first_to_goal_id"] == ana.id and active["leader_id"] == ana.id


# ---- settlement ----


def test_winner_gets_the_bonus_after_the_period(duo, clock):
    rafael, ana = duo
    accepted(rafael, ana)
    train(rafael, clock, 1)
    train(rafael, clock, 2)
    train(ana, clock, 2)
    clock.today = day(7)  # Monday: Sunday still accepts check-ins, the challenge stays open
    assert len(rafael.get("/challenges").json()["active"]) == 1
    before = rafael.balance()

    clock.today = day(8)  # Tuesday: settled
    board = rafael.get("/challenges").json()
    done = board["done"][0]
    assert board["active"] == [] and done["winner_id"] == rafael.id and done["winner_name"] == "Rafael"
    week_win = 20  # the week closes on the same Tuesday: Rafael also won it (100% and more points)
    assert rafael.balance() == before + 20 + week_win
    assert "Você venceu o desafio “Mais treinos”! +20 pts no seu saldo." in rafael.notifications()
    assert "Rafael venceu o desafio “Mais treinos”." in ana.notifications()


def test_tie_and_text_stakes_pay_no_points(duo, clock):
    rafael, ana = duo
    accepted(rafael, ana, workout_type="Aula")  # tie: nobody does an "Aula"
    accepted(rafael, ana, kind="minutes", stake_points=None, stake_text="quem perder faz o jantar")
    train(ana, clock, 3, minutes=60)
    clock.today = day(8)
    done = {c["kind"]: c for c in ana.get("/challenges").json()["done"]}
    assert done["count"]["winner_id"] is None
    assert done["minutes"]["winner_id"] == ana.id
    workout, week_win = 20, 20  # 60 min = 20 pts; Ana also won the week (100% vs 0%)
    assert ana.balance() == workout + week_win  # the text stake adds no points
    assert "Você venceu o desafio “Mais minutos de treino”! Combinado: quem perder faz o jantar." in ana.notifications()


def test_unanswered_challenges_expire(duo, clock):
    rafael, ana = duo
    challenge(rafael)
    clock.today = day(8)
    board = ana.get("/challenges").json()
    assert board["incoming"] == [] and board["done"] == []
