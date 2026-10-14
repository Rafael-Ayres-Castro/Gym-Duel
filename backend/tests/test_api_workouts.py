"""Check-in rules, listing filters and deleting workouts."""

import datetime as dt


def test_checkin_stores_backend_points_and_returns_feedback(rafael, ana):
    response = rafael.checkin(minutes=45, intensity="Alta", note="  Recorde no agachamento  ")
    assert response.status_code == 201
    body = response.json()
    assert body["workout"]["points"] == 20
    assert body["workout"]["note"] == "Recorde no agachamento"
    assert body["workout"]["user_name"] == "Rafael"
    assert body["feedback"]["message"] == "Você passou na frente!"
    assert body["feedback"]["pill"] == "Faltam 3 treinos para sua meta"
    assert body["scoreboard"]["leader_id"] == rafael.id


def test_checkin_only_today_or_yesterday(rafael):
    assert rafael.checkin(days_ago=2).json()["detail"]["code"] == "invalid_date"
    assert rafael.checkin(days_ago=-1).status_code == 422
    assert rafael.checkin(days_ago=1).status_code == 201


def test_one_scored_workout_per_day(rafael):
    assert rafael.checkin().status_code == 201
    second = rafael.checkin(minutes=60)
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "daily_limit"


def test_checkin_validates_fields(rafael):
    assert rafael.checkin(minutes=4).status_code == 422
    assert rafael.checkin(minutes=301).status_code == 422
    assert rafael.checkin(intensity="Extrema").status_code == 422
    assert rafael.checkin(type="Yoga").status_code == 422
    assert rafael.checkin(note="x" * 141).status_code == 422


def test_yesterday_on_monday_goes_to_last_week(rafael, ana, clock):
    clock.today = dt.date(2026, 10, 19)  # Monday
    body = rafael.checkin(days_ago=1).json()
    assert body["feedback"]["counts_for_current_week"] is False
    assert body["feedback"]["message"] == "Registrado na semana anterior."
    assert body["scoreboard"]["players"][0]["done"] == 0


def test_list_filters_by_person_and_period(rafael, ana, clock):
    rafael.checkin(days_ago=0)
    ana.checkin(days_ago=1)

    everyone = rafael.get("/workouts").json()
    assert [w["user_name"] for w in everyone] == ["Rafael", "Ana"]  # newest first
    assert [w["user_name"] for w in rafael.get("/workouts", person="me").json()] == ["Rafael"]
    assert [w["user_name"] for w in rafael.get("/workouts", person="opponent").json()] == ["Ana"]
    assert len(rafael.get("/workouts", limit=1).json()) == 1

    clock.advance(7)  # next week: nothing this week, both still in the month
    assert rafael.get("/workouts", period="week").json() == []
    assert len(rafael.get("/workouts", period="month").json()) == 2
    assert len(rafael.get("/workouts", period="all").json()) == 2


def test_delete_own_workout_removes_points(rafael, ana):
    workout_id = rafael.checkin(minutes=60).json()["workout"]["id"]
    assert rafael.scoreboard()["players"][0]["points"] == 20

    response = rafael.client.delete(f"/api/workouts/{workout_id}", headers=rafael.headers)
    assert response.status_code == 204
    assert rafael.scoreboard()["players"][0]["points"] == 0
    assert rafael.client.delete(f"/api/workouts/{workout_id}", headers=rafael.headers).status_code == 404


def test_cannot_delete_someone_elses_workout(rafael, ana):
    workout_id = ana.checkin().json()["workout"]["id"]
    response = rafael.client.delete(f"/api/workouts/{workout_id}", headers=rafael.headers)
    assert response.status_code == 403
    assert len(ana.get("/workouts", person="me").json()) == 1
