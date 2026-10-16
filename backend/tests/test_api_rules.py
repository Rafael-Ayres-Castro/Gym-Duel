"""Configurable scoring rules: proposal → approval (with recalculation), rejection and cancellation."""

DEFAULTS = {"minutes_per_point": 3, "intensity_adjust": 5, "photo_bonus": 5, "week_winner_bonus": 20}


def proposal(**changes) -> dict:
    return {**DEFAULTS, **changes}


def test_rules_state_has_defaults_options_and_no_proposal(rafael):
    state = rafael.get("/rules").json()
    assert state["current"] == DEFAULTS
    assert state["options"]["minutes_per_point"] == [2, 3, 4]
    assert state["options"]["week_winner_bonus"] == [0, 10, 20, 30]
    assert state["pending"] is None


def test_cannot_propose_without_a_duo(rafael):
    response = rafael.post("/rules/proposals", proposal(minutes_per_point=2))
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "no_duo"


def test_proposal_validation(rafael, ana):
    assert rafael.post("/rules/proposals", proposal(minutes_per_point=5)).status_code == 422
    assert rafael.post("/rules/proposals", proposal(photo_bonus=7)).status_code == 422
    same = rafael.post("/rules/proposals", proposal())
    assert same.status_code == 422 and same.json()["detail"]["code"] == "no_change"


def test_proposal_waits_for_the_other_member(rafael, ana):
    response = rafael.post("/rules/proposals", proposal(minutes_per_point=2))
    assert response.status_code == 201
    mine = response.json()
    assert mine["current"] == DEFAULTS  # nothing changes before approval
    assert mine["pending"]["proposed_by_me"] is True
    assert mine["pending"]["values"]["minutes_per_point"] == 2

    theirs = ana.get("/rules").json()["pending"]
    assert theirs["proposed_by_me"] is False and theirs["proposed_by_name"] == "Rafael"
    assert ana.notifications() == ["Rafael propôs mudar as regras de pontos. Veja em Metas e regras."]

    # Only one proposal at a time, and the author cannot approve their own.
    assert ana.post("/rules/proposals", proposal(photo_bonus=10)).json()["detail"]["code"] == "proposal_pending"
    assert rafael.post(f"/rules/proposals/{theirs['id']}/approve").status_code == 403


def test_approval_recalculates_only_the_current_week(rafael, ana, clock):
    clock.advance(-7)  # last week
    last_week = rafael.checkin(minutes=30).json()["workout"]
    clock.advance(7)  # this week
    this_week = rafael.checkin(minutes=30).json()["workout"]
    assert last_week["points"] == this_week["points"] == 10

    proposal_id = rafael.post("/rules/proposals", proposal(minutes_per_point=2)).json()["pending"]["id"]
    state = ana.post(f"/rules/proposals/{proposal_id}/approve").json()
    assert state["current"]["minutes_per_point"] == 2
    assert state["pending"] is None

    points = {w["id"]: w["points"] for w in rafael.get("/workouts", period="all").json()}
    assert points[this_week["id"]] == 15  # 30 / 2
    assert points[last_week["id"]] == 10  # closed week keeps its points
    assert rafael.scoreboard()["players"][0]["points"] == 15
    assert rafael.scoreboard()["rules"]["minutes_per_point"] == 2
    assert "Ana aprovou as novas regras. Os pontos da semana foram recalculados." in rafael.notifications()

    # New check-ins use the new rules.
    assert ana.checkin(minutes=30).json()["workout"]["points"] == 15


def test_reject_keeps_the_current_rules(rafael, ana):
    proposal_id = rafael.post("/rules/proposals", proposal(intensity_adjust=10)).json()["pending"]["id"]
    assert rafael.post(f"/rules/proposals/{proposal_id}/reject").status_code == 403
    state = ana.post(f"/rules/proposals/{proposal_id}/reject").json()
    assert state["current"] == DEFAULTS and state["pending"] is None
    assert any("recusou" in message for message in rafael.notifications())


def test_only_the_author_cancels(rafael, ana):
    proposal_id = rafael.post("/rules/proposals", proposal(photo_bonus=10)).json()["pending"]["id"]
    assert ana.delete(f"/rules/proposals/{proposal_id}").status_code == 403
    assert rafael.delete(f"/rules/proposals/{proposal_id}").status_code == 204
    assert rafael.get("/rules").json()["pending"] is None
    assert ana.post(f"/rules/proposals/{proposal_id}/approve").json()["detail"]["code"] == "already_decided"
