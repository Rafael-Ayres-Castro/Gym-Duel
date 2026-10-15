"""The rules endpoint mirrors the real scoring rules and settings."""


def test_rules_reflect_scoring_and_settings(rafael):
    rules = rafael.get("/rules").json()
    assert rules["minutes_per_point"] == 3
    assert rules["min_points"] == 5
    assert rules["intensity_adjustment"] == {"Leve": -5, "Moderada": 0, "Alta": 5}
    assert (rules["min_duration_min"], rules["max_duration_min"]) == (5, 300)
    assert (rules["min_weekly_goal"], rules["max_weekly_goal"]) == (1, 7)
    assert rules["max_workouts_per_day"] == 1
    examples = {(e["duration_min"], e["intensity"]): e["points"] for e in rules["examples"]}
    assert examples[(30, "Moderada")] == 10
    assert examples[(45, "Alta")] == 20
    assert examples[(15, "Leve")] == 5  # floor of 5 points


def test_rules_require_login(client):
    assert client.get("/api/rules").status_code == 401
