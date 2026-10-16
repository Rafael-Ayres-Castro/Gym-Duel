"""Screenshots of every screen, to compare with the Claude Design files in design/.

Runs on its own: starts a temporary server with a throwaway database (your real
data is never touched), seeds the demo duo and captures mobile (390×844) and
desktop (1440×900) shots into screenshots/.

    python scripts/screenshots.py

"Today" is pinned to the Thursday of the current week, the same weekday used in
the design, and a second server pinned to Monday captures the empty week.
Needs the dev requirements and `playwright install chromium`.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Browser, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "screenshots"
MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1440, "height": 900}
DEMO = {"rafael": ("rafael@email.com", "gymduel"), "ana": ("ana@email.com", "gymduel")}


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def post(base: str, path: str, body: dict) -> dict:
    request = urllib.request.Request(
        f"{base}{path}", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    return json.load(urllib.request.urlopen(request))


@contextmanager
def server(today: dt.date, seed: bool):
    """Temporary uvicorn with its own SQLite file and APP_TODAY."""
    with tempfile.TemporaryDirectory() as tmp:
        port = free_port()
        env = {
            **os.environ,
            "DATABASE_URL": f"sqlite:///{tmp}/shots.db",
            "APP_TODAY": today.isoformat(),
            "JWT_SECRET": os.environ.get("JWT_SECRET", "screenshots-only-secret-" + "x" * 16),
        }
        if seed:
            subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_demo.py")], env=env, check=True, capture_output=True)
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:create_app", "--factory", "--app-dir", "backend", "--port", str(port)],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        base = f"http://127.0.0.1:{port}"
        try:
            for _ in range(50):
                try:
                    urllib.request.urlopen(f"{base}/api/health")
                    break
                except OSError:
                    time.sleep(0.2)
            yield base
        finally:
            process.terminate()
            process.wait()


def open_page(browser: Browser, base: str, viewport: dict, token: str | None = None):
    page = browser.new_context(viewport=viewport).new_page()
    page.goto(base + "/")
    if token:
        page.evaluate("token => localStorage.setItem('gymduel.token', token)", token)
    return page


def shot(page, name: str, full: bool = False) -> None:
    page.wait_for_timeout(700)  # fonts, bar transitions and confetti
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("  ", name)


def capture_week(browser: Browser, base: str) -> None:
    token = post(base, "/api/auth/login", dict(zip(("email", "password"), DEMO["rafael"])))["access_token"]
    for viewport, tag in ((MOBILE, "mobile"), (DESKTOP, "desktop")):
        page = open_page(browser, base, viewport)
        page.goto(base + "/#/login")
        shot(page, f"{tag}-01-login")
        page.fill("input[name=email]", DEMO["rafael"][0])
        page.fill("input[name=password]", "senha-errada")
        page.click("button[type=submit]")
        page.mouse.move(0, 0)
        shot(page, f"{tag}-02-login-erro")
        page.goto(base + "/#/signup")
        shot(page, f"{tag}-03-cadastro")

        page = open_page(browser, base, viewport, token)
        page.goto(base + "/#/home")
        shot(page, f"{tag}-04-home")
        page.goto(base + "/#/history")
        shot(page, f"{tag}-07-historico")
        for number, route, name in (("08", "challenges", "desafios"), ("09", "rewards", "premios"), ("10", "goals", "metas-e-regras")):
            page.goto(base + f"/#/{route}")
            shot(page, f"{tag}-{number}-{name}", full=True)

    # Check-in and success change the data, so they run once, on mobile, at the end.
    for viewport, tag in ((DESKTOP, "desktop"), (MOBILE, "mobile")):
        page = open_page(browser, base, viewport, token)
        page.goto(base + "/#/home")
        page.wait_for_timeout(500)
        page.click("[data-action=open-checkin] >> visible=true")
        page.click("[data-set=duration][data-value='45']")
        shot(page, f"{tag}-05-checkin")
        if tag == "mobile":
            page.click("[data-action=save]")
            page.wait_for_timeout(600)
            shot(page, f"{tag}-06-sucesso")


def capture_empty_week(browser: Browser, base: str) -> None:
    auth = post(base, "/api/auth/register", {"name": "Rafael", "email": DEMO["rafael"][0], "password": "gymduel", "weekly_goal": 4})
    post(base, "/api/auth/register", {"name": "Ana", "email": DEMO["ana"][0], "password": "gymduel", "weekly_goal": 3})
    for viewport, tag in ((MOBILE, "mobile"), (DESKTOP, "desktop")):
        page = open_page(browser, base, viewport, auth["access_token"])
        page.goto(base + "/#/home")
        shot(page, f"{tag}-04b-home-vazia")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    monday = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        print(f"Semana em andamento (hoje = {monday + dt.timedelta(days=3):%d/%m}):")
        with server(monday + dt.timedelta(days=3), seed=True) as base:
            capture_week(browser, base)
        print(f"Semana vazia (hoje = {monday:%d/%m}):")
        with server(monday, seed=False) as base:
            capture_empty_week(browser, base)
        browser.close()
    print(f"Pronto: {OUT}")


if __name__ == "__main__":
    main()
