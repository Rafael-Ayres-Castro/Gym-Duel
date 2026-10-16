"""Rewards store: creating, redeeming against the balance and the redemption cycle."""


def give_points(player, workouts: int, clock) -> None:
    """Check in on consecutive days (today and yesterday per step) to build up a balance."""
    for day in range(workouts):
        assert player.checkin(minutes=90, intensity="Alta", days_ago=0).status_code == 201  # 35 pts
        clock.advance(1)
    clock.advance(-workouts)


def create_reward(player, title="Massagem nos pés", cost=50):
    response = player.post("/rewards", {"title": title, "cost": cost})
    assert response.status_code == 201, response.text
    return response.json()


def test_create_reward_validates_cost_and_title(rafael):
    assert rafael.post("/rewards", {"title": "Jantar", "cost": 75}).json()["detail"]["code"] == "invalid_cost"
    assert rafael.post("/rewards", {"title": "   ", "cost": 50}).status_code == 422
    assert create_reward(rafael)["created_by"] == rafael.id


def test_store_shows_each_side(rafael, ana):
    create_reward(ana, "Escolher o filme da sexta", 50)
    create_reward(rafael, "Playlist nova de corrida", 100)
    store = rafael.get("/rewards").json()
    assert [r["title"] for r in store["offered_to_me"]] == ["Escolher o filme da sexta"]
    assert [r["title"] for r in store["offered_by_me"]] == ["Playlist nova de corrida"]
    assert (store["balance"], store["opponent_balance"], store["opponent_name"]) == (0, 0, "Ana")
    assert store["costs"] == [50, 100, 150, 200, 300]


def test_redeem_without_balance_is_blocked(rafael, ana):
    reward = create_reward(ana, cost=50)
    rafael.checkin(minutes=30)  # 10 pts
    response = rafael.post(f"/rewards/{reward['id']}/redeem")
    assert response.status_code == 409
    assert response.json()["detail"] == {"code": "insufficient_balance", "message": "Saldo insuficiente: faltam 40 pts."}
    assert rafael.balance() == 10
    assert rafael.get("/redemptions", scope="mine").json() == []


def test_cannot_redeem_own_reward(rafael, ana):
    reward = create_reward(rafael)
    assert rafael.post(f"/rewards/{reward['id']}/redeem").status_code == 403


def test_redeem_debits_balance_but_not_the_scoreboard(rafael, ana, clock):
    reward = create_reward(ana, "Escolher o filme da sexta", 50)
    give_points(rafael, 2, clock)  # 70 pts
    board_before = rafael.scoreboard()["players"][0]

    response = rafael.post(f"/rewards/{reward['id']}/redeem")
    assert response.status_code == 201
    assert response.json()["balance"] == 20
    assert rafael.balance() == 20
    board_after = rafael.scoreboard()["players"][0]
    assert (board_after["points"], board_after["pct"]) == (board_before["points"], board_before["pct"])

    assert ana.notifications() == ["Rafael resgatou “Escolher o filme da sexta”. Veja em Prêmios › Para cumprir."]
    assert ana.get("/badges").json() == {"challenges": 0, "rewards": 1}
    mine = rafael.get("/redemptions", scope="mine").json()
    assert [(r["title"], r["cost"], r["status"], r["owner_name"]) for r in mine] == [
        ("Escolher o filme da sexta", 50, "pending", "Ana")
    ]


def test_redemption_cycle(rafael, ana, clock):
    reward = create_reward(ana, cost=50)
    give_points(rafael, 2, clock)
    redemption_id = rafael.post(f"/rewards/{reward['id']}/redeem").json()["redemption_id"]

    assert rafael.post(f"/redemptions/{redemption_id}/remind").status_code == 204
    assert any("lembrou você" in message for message in ana.notifications())
    assert ana.post(f"/redemptions/{redemption_id}/remind").status_code == 403

    assert rafael.post(f"/redemptions/{redemption_id}/fulfill").status_code == 403  # not the owner
    assert ana.post(f"/redemptions/{redemption_id}/fulfill").status_code == 204
    assert ana.get("/badges").json()["rewards"] == 0
    assert rafael.get("/redemptions", scope="mine").json()[0]["status"] == "fulfilled"
    assert rafael.post(f"/redemptions/{redemption_id}/remind").json()["detail"]["code"] == "not_pending"

    assert ana.post(f"/redemptions/{redemption_id}/receive").status_code == 403  # not who redeemed
    assert rafael.post(f"/redemptions/{redemption_id}/receive").status_code == 204
    assert ana.get("/redemptions", scope="to_fulfill").json()[0]["status"] == "received"
    assert rafael.post(f"/redemptions/{redemption_id}/receive").status_code == 409


def test_redeemer_may_confirm_before_the_owner_marks_it(rafael, ana, clock):
    reward = create_reward(ana, cost=50)
    give_points(rafael, 2, clock)
    redemption_id = rafael.post(f"/rewards/{reward['id']}/redeem").json()["redemption_id"]
    assert rafael.post(f"/redemptions/{redemption_id}/receive").status_code == 204
    assert ana.post(f"/redemptions/{redemption_id}/fulfill").status_code == 409


def test_balance_never_goes_negative_with_repeated_redemptions(rafael, ana, clock):
    reward = create_reward(ana, cost=50)
    give_points(rafael, 2, clock)  # 70 pts: only one redemption fits
    results = [rafael.post(f"/rewards/{reward['id']}/redeem").status_code for _ in range(3)]
    assert results == [201, 409, 409]
    assert rafael.balance() == 20
