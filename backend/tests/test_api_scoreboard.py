"""The weekly duel end to end: leader changes, ties, week turnover, streaks and summaries."""

import datetime as dt


def players_by_name(board: dict) -> dict:
    return {p["name"]: p for p in board["players"]}


def test_scoreboard_waits_for_the_opponent(rafael):
    board = rafael.scoreboard()
    assert board["waiting_for_opponent"] is True
    assert len(board["players"]) == 1
    assert board["leader_id"] is None
    assert board["duel_message"] == "O duelo começa assim que sua dupla se cadastrar."


def test_empty_week(rafael, ana):
    board = rafael.scoreboard()
    assert board["rules"] == {"minutes_per_point": 3, "intensity_adjust": 5, "photo_bonus": 5, "week_winner_bonus": 20}
    assert board["week_start"] == "2026-10-12"
    assert board["week_end"] == "2026-10-18"
    assert board["leader_id"] is None
    assert board["duel_message"] == "Placar zerado. Quem treinar primeiro abre a semana na frente."
    me, opponent = board["players"]
    assert (me["is_me"], me["name"], me["goal"], me["pct"]) == (True, "Rafael", 4, 0)
    assert (opponent["is_me"], opponent["name"], opponent["goal"]) == (False, "Ana", 3)


def test_each_player_sees_themselves_first(rafael, ana):
    assert ana.scoreboard()["players"][0]["name"] == "Ana"


def test_leader_changes_ties_and_delete(rafael, make_player):
    ana = make_player("Ana", "ana@email.com", 2)

    # Ana trains: she leads with 50% (1 of 2); Rafael needs 2 of 4 to catch up.
    ana.checkin(minutes=45, days_ago=1)
    board = rafael.scoreboard()
    assert board["leader_id"] == ana.id
    assert board["duel_message"] == "Ana está na frente. Mais 2 treinos e você empata."

    # Rafael trains twice: 50% vs 50%, and his 20 pts beat her 15.
    rafael.checkin(minutes=30, days_ago=1)
    rafael.checkin(minutes=30, days_ago=0)
    board = rafael.scoreboard()
    assert board["leader_id"] == rafael.id
    assert board["duel_message"] == "Empate na meta. Você lidera nos pontos por 5."
    assert players_by_name(board)["Rafael"]["is_leader"] is True

    # Ana trains again today: 2 of 2 = 100% and she leads.
    ana.checkin(minutes=30, days_ago=0)
    board = rafael.scoreboard()
    assert board["leader_id"] == ana.id
    assert board["duel_message"] == "Ana bateu a meta. Mais 2 treinos e você empata."

    # Ana deletes her last workout: back to 50% vs 50% and Rafael leads on points again.
    last_id = ana.get("/workouts", person="me").json()[0]["id"]
    ana.client.delete(f"/api/workouts/{last_id}", headers=ana.headers)
    assert rafael.scoreboard()["leader_id"] == rafael.id


def test_full_tie_has_no_leader(make_player):
    rafael = make_player("Rafael", "rafael@email.com", 3)
    ana = make_player("Ana", "ana@email.com", 3)
    rafael.checkin(minutes=30)
    ana.checkin(minutes=30)
    board = rafael.scoreboard()
    assert board["leader_id"] is None
    assert board["duel_message"] == "Empate total. O próximo treino desempata."


def test_days_trained_grid(rafael, ana):
    rafael.checkin(days_ago=1)  # Wednesday
    rafael.checkin(days_ago=0)  # Thursday
    me = rafael.scoreboard()["players"][0]
    assert me["days"] == [False, False, True, True, False, False, False]


def test_week_turnover_resets_the_board(rafael, ana, clock):
    rafael.checkin()
    ana.checkin()
    clock.today = dt.date(2026, 10, 18)  # Sunday, same week
    assert rafael.scoreboard()["players"][0]["done"] == 1

    clock.today = dt.date(2026, 10, 19)  # Monday, new week
    board = rafael.scoreboard()
    assert board["week_start"] == "2026-10-19"
    assert [p["done"] for p in board["players"]] == [0, 0]
    assert [p["points"] for p in board["players"]] == [0, 0]
    assert board["leader_id"] is None


def test_streak_counts_weeks_with_goal_met(make_player, clock):
    clock.today = dt.date(2026, 9, 30)  # Wednesday; sign up during week of 28 Sep
    duda = make_player("Duda", "duda@email.com", 2)

    def train_week(monday: dt.date, workouts: int) -> None:
        # Check in on Tue, Wed, ... (today and yesterday only), one per day.
        for i in range(workouts):
            clock.today = monday + dt.timedelta(days=i + 1)
            assert duda.checkin().status_code == 201

    train_week(dt.date(2026, 9, 28), 2)  # met
    train_week(dt.date(2026, 10, 5), 1)  # missed
    train_week(dt.date(2026, 10, 12), 2)  # met
    train_week(dt.date(2026, 10, 19), 2)  # met

    clock.today = dt.date(2026, 10, 26)  # Monday after: two closed weeks in a row
    assert duda.scoreboard()["players"][0]["streak"] == 2

    clock.today = dt.date(2026, 10, 28)
    assert duda.checkin().status_code == 201
    assert duda.scoreboard()["players"][0]["streak"] == 2  # 1 of 2 this week: not yet
    clock.today = dt.date(2026, 10, 29)
    body = duda.checkin().json()
    assert body["scoreboard"]["players"][0]["streak"] == 3  # current week met adds one
    assert body["feedback"]["pill"] == "Meta batida · sequência de 3 semanas"


def test_summary_per_period(rafael, ana, clock):
    rafael.checkin(minutes=60)
    ana.checkin(minutes=30, days_ago=1)
    week = {p["name"]: p for p in rafael.get("/summary", period="week").json()["players"]}
    assert (week["Rafael"]["workouts"], week["Rafael"]["points"], week["Rafael"]["pct"]) == (1, 20, 25)
    assert (week["Ana"]["workouts"], week["Ana"]["points"], week["Ana"]["pct"]) == (1, 10, 33)

    clock.advance(7)
    month = rafael.get("/summary", period="month").json()
    assert month["start"] == "2026-10-01"
    assert [p["workouts"] for p in month["players"]] == [1, 1]
    assert [p["workouts"] for p in rafael.get("/summary", period="week").json()["players"]] == [0, 0]
