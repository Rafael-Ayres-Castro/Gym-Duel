"""Create the demo duo (Rafael and Ana) with the 16 workouts of the prototype.

Dates are relative to the current week: in the prototype, day 13 is the Monday of
the week on screen, so day 16 becomes this week's Thursday, day 6 last week's
Monday, and so on. Workouts that would fall after today are skipped.

Usage (from the project root, with the venv active):
    python scripts/seed_demo.py           # refuses to run if there are users
    python scripts/seed_demo.py --reset   # wipes the database first

The demo password lives only in this script.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import func, select, text  # noqa: E402

from app.clock import today_in_sao_paulo  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import Base, make_engine, make_session_factory  # noqa: E402
from app.migrate import upgrade_to_head  # noqa: E402
from app.models import User, Workout  # noqa: E402
from app.scoring import calc_points, week_bounds  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.services.players import set_goal  # noqa: E402

DEMO_PASSWORD = "gymduel"
PLAYERS = {
    "R": ("Rafael", "rafael@email.com", 4),
    "A": ("Ana", "ana@email.com", 3),
}
PROTOTYPE_MONDAY = 13
# (who, type, minutes, intensity, prototype day, note), newest first: copied from SEED in the prototype.
SEED = [
    ("A", "Funcional", 45, "Alta", 16, ""),
    ("R", "Musculação", 60, "Moderada", 15, "Treino de costas"),
    ("A", "Corrida", 30, "Moderada", 15, ""),
    ("A", "Aula", 60, "Alta", 14, "Spinning"),
    ("R", "Corrida", 30, "Moderada", 14, ""),
    ("R", "Musculação", 45, "Moderada", 13, ""),
    ("R", "Corrida", 45, "Moderada", 12, ""),
    ("A", "Aula", 60, "Alta", 10, ""),
    ("R", "Musculação", 60, "Moderada", 10, ""),
    ("R", "Musculação", 45, "Alta", 8, "Recorde no agachamento"),
    ("A", "Funcional", 45, "Moderada", 8, ""),
    ("A", "Corrida", 45, "Moderada", 6, ""),
    ("R", "Funcional", 30, "Leve", 6, ""),
    ("A", "Musculação", 45, "Moderada", 4, ""),
    ("R", "Musculação", 60, "Moderada", 2, ""),
    ("A", "Aula", 60, "Moderada", 2, ""),
]
# Older weeks, to give the streak panel some history: 1 = goal met, 0 = missed (HIST in the prototype),
# oldest first, ending two weeks before the oldest SEED week.
HISTORY = {"R": [1, 1, 1, 0, 1, 0], "A": [1, 1, 1, 1, 1, 0]}
HISTORY_DAYS = {"R": (0, 2, 4, 5), "A": (1, 3, 5)}  # weekday offsets used for filler workouts
HISTORY_TYPES = ("Musculação", "Corrida", "Funcional", "Aula")


def history_workouts(first_seed_week: dt.date) -> list[tuple[str, str, int, str, dt.date]]:
    """Filler workouts for HISTORY: `goal` workouts in a met week, two fewer in a missed one."""
    rows = []
    for who, weeks in HISTORY.items():
        goal = PLAYERS[who][2]
        for index, met in enumerate(weeks):
            week_start = first_seed_week - dt.timedelta(weeks=len(weeks) - index)
            count = goal if met else max(0, goal - 2)
            for n, offset in enumerate(HISTORY_DAYS[who][:count]):
                rows.append((who, HISTORY_TYPES[(index + n) % len(HISTORY_TYPES)], 45, "Moderada", week_start + dt.timedelta(days=offset)))
    return rows


def seed(reset: bool) -> None:
    settings = get_settings()
    engine = make_engine(settings.database_url)
    if reset:
        Base.metadata.drop_all(engine)
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    upgrade_to_head(engine)
    today = today_in_sao_paulo(settings)
    monday = week_bounds(today)[0]

    with make_session_factory(engine)() as db:
        if db.scalar(select(func.count()).select_from(User)):
            sys.exit("Já existem usuários no banco. Use --reset para apagar tudo e recriar a demonstração.")

        # Goals start on the week of the oldest workout, so past weeks count for the streak.
        first_seed_week = week_bounds(monday + dt.timedelta(days=min(day for *_, day, _ in SEED) - PROTOTYPE_MONDAY))[0]
        first_week = first_seed_week - dt.timedelta(weeks=len(HISTORY["R"]))
        users = {}
        for key, (name, email, goal) in PLAYERS.items():
            user = User(name=name, email=email, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.flush()
            set_goal(db, user.id, goal, first_week)
            users[key] = user

        skipped = 0
        for position, (who, kind, minutes, intensity, day, note) in enumerate(SEED):
            date = monday + dt.timedelta(days=day - PROTOTYPE_MONDAY)
            if date > today:
                skipped += 1
                continue
            # Same-day workouts keep the prototype order (earlier in SEED = registered later).
            created = dt.datetime.combine(date, dt.time(20, 0), tzinfo=dt.UTC) - dt.timedelta(minutes=position)
            db.add(
                Workout(
                    user_id=users[who].id, date=date, type=kind, duration_min=minutes, intensity=intensity,
                    points=calc_points(minutes, intensity), note=note, created_at=created,
                )
            )
        history = history_workouts(first_seed_week)
        for who, kind, minutes, intensity, date in history:
            db.add(
                Workout(
                    user_id=users[who].id, date=date, type=kind, duration_min=minutes, intensity=intensity,
                    points=calc_points(minutes, intensity), note="",
                    created_at=dt.datetime.combine(date, dt.time(19, 0), tzinfo=dt.UTC),
                )
            )
        db.commit()

    print(f"Demonstração criada (hoje = {today:%d/%m/%Y}).")
    for name, email, goal in PLAYERS.values():
        print(f"  {name}: {email} / senha {DEMO_PASSWORD} (meta {goal})")
    note = f" ({skipped} pulados por cair depois de hoje)" if skipped else ""
    print(f"  {len(SEED) - skipped} treinos da semana do protótipo{note} + {len(history)} de histórico")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="apaga todos os dados antes de criar a demonstração")
    seed(parser.parse_args().reset)
