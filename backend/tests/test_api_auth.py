"""Sign up, log in, the two-player limit and the profile endpoints."""

from conftest import register


def test_register_returns_token_and_user(client):
    response = register(client, "Rafael Castro", "Rafael@Email.com", 4)
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "rafael@email.com"
    assert body["user"]["first_name"] == "Rafael"
    assert body["user"]["weekly_goal"] == 4
    assert body["user"]["color"] == "blue"


def test_second_player_is_pink_and_third_is_blocked(client, rafael, ana):
    assert ana.user["color"] == "pink"
    response = register(client, "Intrusa", "intrusa@email.com", 3)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "registration_closed"


def test_register_rejects_duplicate_email(client, rafael):
    response = register(client, "Outro", "RAFAEL@email.com", 3)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "email_taken"


def test_register_validates_input(client):
    assert register(client, "Ana", "ana@email.com", 0).status_code == 422
    assert register(client, "Ana", "ana@email.com", 8).status_code == 422
    assert register(client, "Ana", "nao-e-email", 3).status_code == 422
    assert register(client, "Ana", "ana@email.com", 3, password="123").status_code == 422
    assert register(client, "   ", "ana@email.com", 3).status_code == 422


def test_login_success_and_errors(client, rafael):
    ok = client.post("/api/auth/login", json={"email": " RAFAEL@email.com ", "password": "segredo123"})
    assert ok.status_code == 200
    assert ok.json()["user"]["id"] == rafael.id

    wrong = client.post("/api/auth/login", json={"email": "rafael@email.com", "password": "errada"})
    assert wrong.status_code == 401
    assert wrong.json()["detail"] == {"code": "wrong_password", "message": "Senha incorreta. Confira e tente de novo."}

    unknown = client.post("/api/auth/login", json={"email": "ninguem@email.com", "password": "x"})
    assert unknown.status_code == 401
    assert unknown.json()["detail"]["code"] == "unknown_email"


def test_health_is_public(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_frontend_is_served_at_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Gym Duel" in response.text


def test_routes_require_token(client):
    for path in ("/api/me", "/api/workouts", "/api/scoreboard", "/api/summary"):
        assert client.get(path).status_code == 401
    bad = client.get("/api/me", headers={"Authorization": "Bearer lixo"})
    assert bad.status_code == 401


def test_get_and_patch_me(rafael):
    me = rafael.get("/me").json()
    assert (me["name"], me["weekly_goal"], me["next_weekly_goal"], me["balance"]) == ("Rafael Castro", 4, None, 0)
    response = rafael.client.patch("/api/me", headers=rafael.headers, json={"weekly_goal": 5, "name": "Rafa"})
    assert response.status_code == 200
    assert response.json()["weekly_goal"] == 4  # this week keeps its goal
    assert response.json()["next_weekly_goal"] == 5
    assert response.json()["first_name"] == "Rafa"


def test_choosing_the_current_goal_drops_the_scheduled_change(rafael):
    rafael.client.patch("/api/me", headers=rafael.headers, json={"weekly_goal": 6})
    response = rafael.client.patch("/api/me", headers=rafael.headers, json={"weekly_goal": 4})
    assert response.json()["next_weekly_goal"] is None


def test_goal_change_applies_from_next_week_and_keeps_the_past(rafael, clock):
    # Rafael meets his goal of 4 this week...
    for days_ago in (0, 1):
        assert rafael.checkin(days_ago=days_ago).status_code == 201  # Thu and Wed
    clock.advance(2)  # Saturday
    for days_ago in (0, 1):
        assert rafael.checkin(days_ago=days_ago).status_code == 201  # Sat and Fri

    # ...and raises it to 6: the scoreboard of the week in course does not move.
    rafael.client.patch("/api/me", headers=rafael.headers, json={"weekly_goal": 6})
    me = rafael.scoreboard()["players"][0]
    assert (me["goal"], me["pct"], me["streak"]) == (4, 100, 1)

    clock.advance(5)  # Thursday of the next week: the new goal is in force
    me = rafael.scoreboard()["players"][0]
    assert (me["goal"], me["streak"]) == (6, 1)  # last week stays met with its goal of 4
