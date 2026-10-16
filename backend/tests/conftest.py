"""Shared fixtures: an isolated app per test with its own SQLite file and a controllable clock."""

from __future__ import annotations

import datetime as dt

import bcrypt
import pytest
from fastapi.testclient import TestClient

from app import security
from app.clock import get_today
from app.config import Settings
from app.main import create_app

THURSDAY = dt.date(2026, 10, 15)  # Week of Mon 12 to Sun 18 Oct 2026


class FakeClock:
    """Mutable "today" so a test can move through days and weeks."""

    def __init__(self, today: dt.date) -> None:
        self.today = today

    def advance(self, days: int) -> None:
        self.today += dt.timedelta(days=days)


@pytest.fixture(autouse=True)
def fast_bcrypt(monkeypatch):
    # The default cost (12) makes each sign up take ~0.3 s; tests only need correctness.
    real_gensalt = bcrypt.gensalt
    monkeypatch.setattr(security.bcrypt, "gensalt", lambda: real_gensalt(rounds=4))


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(THURSDAY)


@pytest.fixture
def client(tmp_path, clock):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        jwt_secret="test-secret-" + "x" * 32,
        max_users=2,
        max_workouts_per_day=1,
        auto_migrate=False,
    )
    app = create_app(settings)
    app.dependency_overrides[get_today] = lambda: clock.today
    with TestClient(app) as test_client:
        yield test_client


class Player:
    """A signed-up user and helpers to call the API as them."""

    def __init__(self, client: TestClient, clock: FakeClock, auth: dict) -> None:
        self.client = client
        self.clock = clock
        self.id = auth["user"]["id"]
        self.user = auth["user"]
        self.headers = {"Authorization": f"Bearer {auth['access_token']}"}

    def get(self, path: str, **params):
        return self.client.get(f"/api{path}", headers=self.headers, params=params)

    def post(self, path: str, json: dict | None = None):
        return self.client.post(f"/api{path}", headers=self.headers, json=json)

    def patch(self, path: str, json: dict):
        return self.client.patch(f"/api{path}", headers=self.headers, json=json)

    def delete(self, path: str):
        return self.client.delete(f"/api{path}", headers=self.headers)

    def balance(self) -> int:
        return self.get("/me").json()["balance"]

    def notifications(self) -> list[str]:
        return [n["message"] for n in self.get("/notifications").json()]

    def checkin(self, minutes: int = 30, intensity: str = "Moderada", days_ago: int = 0, **extra):
        body = {
            "type": extra.pop("type", "Musculação"),
            "duration_min": minutes,
            "intensity": intensity,
            "date": (self.clock.today - dt.timedelta(days=days_ago)).isoformat(),
            **extra,
        }
        return self.client.post("/api/workouts", headers=self.headers, json=body)

    def scoreboard(self) -> dict:
        response = self.get("/scoreboard")
        assert response.status_code == 200, response.text
        return response.json()


def register(client: TestClient, name: str, email: str, goal: int, password: str = "segredo123"):
    return client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password, "weekly_goal": goal},
    )


@pytest.fixture
def make_player(client, clock):
    def _make(name: str, email: str, goal: int) -> Player:
        response = register(client, name, email, goal)
        assert response.status_code == 201, response.text
        return Player(client, clock, response.json())

    return _make


@pytest.fixture
def rafael(make_player) -> Player:
    return make_player("Rafael Castro", "rafael@email.com", 4)


@pytest.fixture
def ana(make_player, rafael) -> Player:
    return make_player("Ana", "ana@email.com", 3)
