"""Challenges between the two members: create → accept/decline → progress → close.

Progress is derived from the workouts inside the period (never stored). Rules:
- "Mais treinos" / "Mais minutos": the higher value wins; a tie has no winner.
- "Primeiro a bater a meta" (week only): who reached 100% of their goal first, by training
  date and then check-in time; if nobody reached it, there is no winner.
- Points are only a bonus for the winner (ledger); nobody loses points.
- A challenge closes when its period can no longer receive check-ins (the day after
  "ontem" passes), like the weeks. Pending challenges whose period ended are removed.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .. import scoring, texts
from ..errors import api_error
from ..models import Challenge, User, Workout
from ..scoring import week_bounds
from . import ledger, notifications, players
from .weeks import CHECKIN_WINDOW_DAYS

DONE_LIMIT = 10


# ---- Period and progress ----


def period_dates(period: str, today: dt.date) -> tuple[dt.date, dt.date]:
    monday, sunday = week_bounds(today)
    return (sunday - dt.timedelta(days=1), sunday) if period == "weekend" else (monday, sunday)


def _workouts(db: Session, challenge: Challenge, user_id: int) -> list[Workout]:
    stmt = select(Workout).where(
        Workout.user_id == user_id, Workout.date >= challenge.starts_on, Workout.date <= challenge.ends_on
    )
    if challenge.workout_type:
        stmt = stmt.where(Workout.type == challenge.workout_type)
    return list(db.scalars(stmt))


def _goal(db: Session, user_id: int, week_start: dt.date) -> int:
    return players.goal_for_week(players.goals_by_week(db, user_id), week_start) or 1


def progress(db: Session, challenge: Challenge) -> dict:
    """Value of each member, who is ahead now and (goal challenges) who reached the goal first."""
    members = (challenge.created_by, challenge.challenged_id)
    values: dict[int, int] = {}
    reached: dict[int, tuple | None] = {}
    for user_id in members:
        workouts = _workouts(db, challenge, user_id)
        if challenge.kind == "count":
            values[user_id] = len(workouts)
        elif challenge.kind == "minutes":
            values[user_id] = sum(w.duration_min for w in workouts)
        else:
            goal = _goal(db, user_id, challenge.starts_on)
            values[user_id] = scoring.pct(len(workouts), goal)
            reached[user_id] = scoring.goal_reached_at([(w.date, w.created_at) for w in workouts], goal)

    if challenge.kind == "goal":
        first = scoring.first_to_reach(reached)
        leader = first if first is not None else scoring.higher_value_winner(values)
        return {"values": values, "leader_id": leader, "first_to_goal_id": first}
    return {"values": values, "leader_id": scoring.higher_value_winner(values), "first_to_goal_id": None}


def winner_of(db: Session, challenge: Challenge) -> int | None:
    result = progress(db, challenge)
    return result["first_to_goal_id"] if challenge.kind == "goal" else result["leader_id"]


# ---- Lifecycle ----


def create(db: Session, user: User, data, today: dt.date) -> Challenge:
    opponent = players.opponent_of(db, user)
    if opponent is None:
        raise api_error(409, "no_duo", "Sua dupla precisa estar cadastrada para receber desafios.")
    starts_on, ends_on = period_dates(data.period, today)
    challenge = Challenge(
        created_by=user.id, challenged_id=opponent.id, kind=data.kind, workout_type=data.workout_type,
        period=data.period, starts_on=starts_on, ends_on=ends_on,
        stake_points=data.stake_points, stake_text=data.stake_text,
    )
    db.add(challenge)
    db.flush()
    title = texts.challenge_title(challenge.kind, challenge.workout_type, challenge.period)
    notifications.notify(
        db, opponent.id, "challenge_received",
        f"{players.display_name(user)} te desafiou: {title.lower()}. Responda em Desafios.",
        {"challenge_id": challenge.id},
    )
    db.commit()
    return challenge


def _get(db: Session, challenge_id: int, status: str) -> Challenge:
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise api_error(404, "not_found", "Desafio não encontrado.")
    if challenge.status != status:
        raise api_error(409, "wrong_status", "Esse desafio já mudou de situação.")
    return challenge


def accept(db: Session, user: User, challenge_id: int) -> None:
    challenge = _get(db, challenge_id, "pending")
    if challenge.challenged_id != user.id:
        raise api_error(403, "not_challenged", "Só quem foi desafiado pode aceitar.")
    challenge.status = "active"
    challenge.accepted_at = dt.datetime.now(dt.UTC)
    title = texts.challenge_title(challenge.kind, challenge.workout_type, challenge.period)
    notifications.notify(
        db, challenge.created_by, "challenge_accepted", f"{players.display_name(user)} aceitou o desafio: {title.lower()}. Boa sorte!"
    )
    db.commit()


def decline(db: Session, user: User, challenge_id: int) -> None:
    """Turning a challenge down removes it, and the author is told."""
    challenge = _get(db, challenge_id, "pending")
    if challenge.challenged_id != user.id:
        raise api_error(403, "not_challenged", "Só quem foi desafiado pode recusar.")
    title = texts.challenge_title(challenge.kind, challenge.workout_type, challenge.period)
    db.delete(challenge)
    notifications.notify(db, challenge.created_by, "challenge_declined", f"{players.display_name(user)} recusou o desafio: {title.lower()}.")
    db.commit()


def cancel(db: Session, user: User, challenge_id: int) -> None:
    challenge = _get(db, challenge_id, "pending")
    if challenge.created_by != user.id:
        raise api_error(403, "not_author", "Só quem criou o desafio pode cancelar.")
    db.delete(challenge)
    db.commit()


def close_finished(db: Session, today: dt.date) -> None:
    """Settle active challenges whose period can no longer change; drop expired pending ones."""
    last_closed_day = today - dt.timedelta(days=CHECKIN_WINDOW_DAYS + 1)
    db.execute(delete(Challenge).where(Challenge.status == "pending", Challenge.ends_on <= last_closed_day))
    finished = list(db.scalars(select(Challenge).where(Challenge.status == "active", Challenge.ends_on <= last_closed_day)))
    for challenge in finished:
        winner_id = winner_of(db, challenge)
        challenge.status = "done"
        challenge.winner_id = winner_id
        challenge.closed_at = dt.datetime.now(dt.UTC)
        _announce(db, challenge, winner_id)
    db.commit()


def _announce(db: Session, challenge: Challenge, winner_id: int | None) -> None:
    title = texts.challenge_title(challenge.kind, challenge.workout_type)
    members = (challenge.created_by, challenge.challenged_id)
    if winner_id is None:
        for user_id in members:
            notifications.notify(db, user_id, "challenge_tied", f"O desafio “{title}” terminou sem vencedor.")
        return
    loser_id = members[1] if winner_id == members[0] else members[0]
    prize = f" +{challenge.stake_points} pts no seu saldo." if challenge.stake_points else f" Combinado: {challenge.stake_text}."
    if challenge.stake_points:
        ledger.add(db, winner_id, "challenge", challenge.stake_points, challenge.id)
    winner_name = players.display_name(db.get(User, winner_id))
    notifications.notify(db, winner_id, "challenge_won", f"Você venceu o desafio “{title}”!{prize}")
    notifications.notify(db, loser_id, "challenge_lost", f"{winner_name} venceu o desafio “{title}”.")


# ---- Listing ----


def _challenge_out(db: Session, challenge: Challenge, viewer: User) -> dict:
    author = db.get(User, challenge.created_by)
    result = progress(db, challenge) if challenge.status != "done" else None
    rows = []
    for user_id in (viewer.id, challenge.challenged_id if viewer.id == challenge.created_by else challenge.created_by):
        member = db.get(User, user_id)
        rows.append(
            {
                "user_id": user_id,
                "name": players.display_name(member),
                "color": players.player_color(db, member),
                "is_me": user_id == viewer.id,
                "value": result["values"][user_id] if result else 0,
            }
        )
    winner = db.get(User, challenge.winner_id) if challenge.winner_id else None
    return {
        "id": challenge.id,
        "title": texts.challenge_title(challenge.kind, challenge.workout_type, challenge.period),
        "base_title": texts.challenge_title(challenge.kind, challenge.workout_type),
        "kind": challenge.kind,
        "workout_type": challenge.workout_type,
        "period": challenge.period,
        "starts_on": challenge.starts_on,
        "ends_on": challenge.ends_on,
        "stake_points": challenge.stake_points,
        "stake_text": challenge.stake_text,
        "status": challenge.status,
        "created_by_me": challenge.created_by == viewer.id,
        "created_by_name": players.display_name(author),
        "players": rows,
        "leader_id": result["leader_id"] if result else None,
        "first_to_goal_id": result["first_to_goal_id"] if result else None,
        "winner_id": challenge.winner_id,
        "winner_name": players.display_name(winner) if winner else None,
        "winner_color": players.player_color(db, winner) if winner else None,
    }


def board(db: Session, viewer: User) -> dict:
    mine = (Challenge.created_by == viewer.id) | (Challenge.challenged_id == viewer.id)
    by_status = lambda status: select(Challenge).where(mine, Challenge.status == status)  # noqa: E731
    pending = list(db.scalars(by_status("pending").order_by(Challenge.created_at.desc())))
    active = db.scalars(by_status("active").order_by(Challenge.ends_on, Challenge.id))
    done = db.scalars(by_status("done").order_by(Challenge.ends_on.desc(), Challenge.id.desc()).limit(DONE_LIMIT))
    out = lambda challenge: _challenge_out(db, challenge, viewer)  # noqa: E731
    return {
        "incoming": [out(c) for c in pending if c.challenged_id == viewer.id],
        "outgoing": [out(c) for c in pending if c.created_by == viewer.id],
        "active": [out(c) for c in active],
        "done": [out(c) for c in done],
    }


def incoming_count(db: Session, user: User) -> int:
    stmt = select(func.count()).select_from(Challenge).where(Challenge.challenged_id == user.id, Challenge.status == "pending")
    return db.scalar(stmt) or 0
