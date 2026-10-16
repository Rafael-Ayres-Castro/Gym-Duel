"""Account screen: changing e-mail and password (with the current password) and the all-time stats."""


def login(client, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def put(player, path: str, body: dict):
    return player.client.put(f"/api{path}", headers=player.headers, json=body)


# ---- E-mail ----


def test_change_email_then_login_with_the_new_one(client, rafael):
    response = put(rafael, "/me/email", {"email": " Rafa@Novo.com ", "current_password": "segredo123"})
    assert response.status_code == 200, response.text
    assert response.json()["email"] == "rafa@novo.com"
    assert login(client, "rafa@novo.com", "segredo123").status_code == 200
    assert login(client, "rafael@email.com", "segredo123").json()["detail"]["code"] == "unknown_email"


def test_change_email_asks_for_the_current_password(rafael):
    response = put(rafael, "/me/email", {"email": "rafa@novo.com", "current_password": "errada"})
    # 403 and not 401: a wrong confirmation must not look like an expired session.
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "wrong_password"
    assert rafael.get("/me").json()["email"] == "rafael@email.com"


def test_change_email_rejects_taken_and_invalid_addresses(rafael, ana):
    taken = put(rafael, "/me/email", {"email": "ANA@email.com", "current_password": "segredo123"})
    assert taken.status_code == 409
    assert taken.json()["detail"]["code"] == "email_taken"
    assert put(rafael, "/me/email", {"email": "nao-e-email", "current_password": "segredo123"}).status_code == 422


def test_keeping_the_same_email_is_fine(rafael):
    response = put(rafael, "/me/email", {"email": "rafael@email.com", "current_password": "segredo123"})
    assert response.status_code == 200


# ---- Password ----


def test_change_password_keeps_the_session_and_swaps_the_login(client, rafael):
    response = put(rafael, "/me/password", {"current_password": "segredo123", "new_password": "nova-senha"})
    assert response.status_code == 204
    assert rafael.get("/me").status_code == 200  # the token in use stays valid
    assert login(client, "rafael@email.com", "nova-senha").status_code == 200
    assert login(client, "rafael@email.com", "segredo123").json()["detail"]["code"] == "wrong_password"


def test_change_password_errors(rafael):
    wrong = put(rafael, "/me/password", {"current_password": "errada", "new_password": "nova-senha"})
    assert (wrong.status_code, wrong.json()["detail"]["code"]) == (403, "wrong_password")
    same = put(rafael, "/me/password", {"current_password": "segredo123", "new_password": "segredo123"})
    assert (same.status_code, same.json()["detail"]["code"]) == (422, "same_password")
    assert put(rafael, "/me/password", {"current_password": "segredo123", "new_password": "123"}).status_code == 422
    too_long = "ç" * 40  # 80 bytes: bcrypt would silently cut it
    assert put(rafael, "/me/password", {"current_password": "segredo123", "new_password": too_long}).status_code == 422


def test_account_routes_require_a_token(client):
    assert client.put("/api/me/password", json={"current_password": "x", "new_password": "123456"}).status_code == 401
    assert client.get("/api/me/stats").status_code == 401


# ---- Stats ----


def test_stats_of_a_new_player_are_zero(rafael):
    stats = rafael.get("/me/stats").json()
    assert stats["workouts"] == stats["minutes"] == stats["points_earned"] == stats["weeks_closed"] == 0
    assert stats["favorite_type"] is None


def test_stats_add_up_workouts_weeks_and_balance(rafael, ana, clock):
    rafael.checkin(minutes=60, type="Corrida")
    rafael.checkin(minutes=30, days_ago=1, type="Corrida")
    clock.advance(1)
    rafael.checkin(minutes=45, type="Musculação")
    clock.advance(4)  # Tuesday of the next week: last week is closed and Rafael won it (75% x 0%)

    stats = rafael.get("/me/stats").json()
    assert (stats["workouts"], stats["minutes"], stats["favorite_type"]) == (3, 135, "Corrida")
    assert (stats["weeks_closed"], stats["weeks_won"], stats["weeks_goal_met"]) == (1, 1, 0)
    assert (stats["streak"], stats["record"], stats["badges"]) == (0, 0, 0)
    # Earned (workouts + bonuses) minus spent is always the balance.
    assert stats["points_earned"] - stats["points_spent"] == rafael.balance()
    assert stats["points_earned"] > sum(w["points"] for w in rafael.get("/workouts", period="all").json())

    ana_stats = ana.get("/me/stats").json()
    assert (ana_stats["weeks_closed"], ana_stats["weeks_won"], ana_stats["workouts"]) == (1, 0, 0)
