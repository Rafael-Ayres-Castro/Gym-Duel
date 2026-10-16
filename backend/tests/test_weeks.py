"""Closing weeks: when it happens, winner bonus, streak badges, balance and the streaks panel."""

import datetime as dt

MONDAY = dt.date(2026, 10, 12)


def day(offset: int) -> dt.date:
    return MONDAY + dt.timedelta(days=offset)


def train(player, clock, *days: int, minutes: int = 30) -> None:
    """Check in on the given days (offsets from MONDAY), each one as "today"."""
    for offset in days:
        clock.today = day(offset)
        assert player.checkin(minutes=minutes).status_code == 201


def test_week_closes_on_tuesday_and_pays_the_winner(make_player, clock):
    clock.today = MONDAY
    rafael = make_player("Rafael", "rafael@email.com", 2)
    ana = make_player("Ana", "ana@email.com", 2)
    train(rafael, clock, 2, 3)  # Wed, Thu: 2 of 2 = 100%
    train(ana, clock, 3)  # Thu: 50%
    workouts_points = 20

    clock.today = day(7)  # next Monday: Sunday can still get a check-in, nothing closes
    assert rafael.balance() == workouts_points

    clock.today = day(8)  # Tuesday: last week closes
    assert rafael.balance() == workouts_points + 20
    assert ana.balance() == 10
    assert rafael.notifications() == ["Você venceu a semana de 12 a 18 de out! +20 pts no seu saldo."]

    # Idempotent: more requests do not pay twice.
    rafael.scoreboard()
    ana.scoreboard()
    assert rafael.balance() == workouts_points + 20


def test_tie_gives_no_winner_bonus(make_player, clock):
    clock.today = MONDAY
    rafael = make_player("Rafael", "rafael@email.com", 1)
    ana = make_player("Ana", "ana@email.com", 1)
    train(rafael, clock, 1)
    train(ana, clock, 1)
    clock.today = day(8)
    assert rafael.balance() == ana.balance() == 10


def test_winner_bonus_follows_the_rules_of_that_week(make_player, clock):
    clock.today = MONDAY
    rafael = make_player("Rafael", "rafael@email.com", 1)
    ana = make_player("Ana", "ana@email.com", 1)
    proposal = {"minutes_per_point": 3, "intensity_adjust": 5, "photo_bonus": 5, "week_winner_bonus": 30}
    proposal_id = rafael.post("/rules/proposals", proposal).json()["pending"]["id"]
    ana.post(f"/rules/proposals/{proposal_id}/approve")
    train(rafael, clock, 1)
    clock.today = day(8)
    assert rafael.balance() == 10 + 30


def test_two_weeks_in_a_row_earn_the_first_badge(make_player, clock):
    clock.today = MONDAY
    rafael = make_player("Rafael", "rafael@email.com", 1)
    make_player("Ana", "ana@email.com", 3)
    train(rafael, clock, 1, 8)  # one workout in each week (goal 1)
    clock.today = day(15)  # Tuesday after the second week

    workouts, wins, badge = 20, 20 + 20, 10  # he also won both weeks (100% vs 0%)
    assert rafael.balance() == workouts + wins + badge
    streaks = rafael.get("/streaks").json()["players"][0]
    assert (streaks["streak"], streaks["record"]) == (2, 2)
    assert [b["earned"] for b in streaks["badges"]] == [True, False, False, False]
    assert streaks["next_badge"] == {"milestone": 4, "weeks_left": 2}
    assert "Selo de 2 semanas seguidas com a meta batida! +10 pts no seu saldo." in rafael.notifications()


def test_missed_week_resets_streak_but_keeps_record_and_points(make_player, clock):
    clock.today = MONDAY
    rafael = make_player("Rafael", "rafael@email.com", 1)
    train(rafael, clock, 1, 8)  # met, met
    clock.today = day(22)  # Tuesday after a week with no workout
    streaks = rafael.get("/streaks").json()["players"][0]
    assert (streaks["streak"], streaks["record"]) == (0, 2)
    assert rafael.balance() == 20 + 10  # workouts + badge (alone, there is no week winner)
    weeks = streaks["weeks"]
    assert len(weeks) == 9 and weeks[-1]["is_current"]
    assert [w["met"] for w in weeks[-4:]] == [True, True, False, False]
    assert weeks[0]["goal"] is None  # before sign up


def test_current_week_counts_in_the_streak_once_met(make_player, clock):
    clock.today = MONDAY
    rafael = make_player("Rafael", "rafael@email.com", 1)
    first = rafael.get("/streaks").json()["players"][0]
    assert (first["streak"], first["weeks"][-1]["done"], first["weeks"][-1]["goal"]) == (0, 0, 1)
    train(rafael, clock, 0)
    assert rafael.get("/streaks").json()["players"][0]["streak"] == 1


def test_streaks_lists_both_players_me_first(rafael, ana):
    players = ana.get("/streaks").json()["players"]
    assert [p["name"] for p in players] == ["Ana", "Rafael"]
    assert [p["is_me"] for p in players] == [True, False]


def test_notifications_are_marked_as_read(rafael, ana):
    rafael.post("/rules/proposals", {"minutes_per_point": 2, "intensity_adjust": 5, "photo_bonus": 5, "week_winner_bonus": 20})
    assert len(ana.notifications()) == 1
    assert ana.post("/notifications/read").status_code == 204
    assert ana.notifications() == []
