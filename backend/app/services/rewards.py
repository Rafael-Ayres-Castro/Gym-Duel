"""Rewards store: rewards offered by each member, redemptions paid from the balance.

The balance is separate from the weekly scoreboard: redeeming lowers the balance
(a negative ledger entry) and never touches workouts or week results.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..clock import local_date
from ..errors import api_error
from ..models import Redemption, Reward, User
from . import ledger, notifications, players

REWARD_COSTS = (50, 100, 150, 200, 300)


def _reward_out(reward: Reward) -> dict:
    return {"id": reward.id, "title": reward.title, "cost": reward.cost, "created_by": reward.created_by}


def store(db: Session, user: User) -> dict:
    """Balances plus the two shelves: offered by the duo (you redeem) and offered by you (they redeem)."""
    opponent = players.opponent_of(db, user)
    active = select(Reward).where(Reward.active.is_(True)).order_by(Reward.cost, Reward.id)
    return {
        "balance": ledger.balance(db, user.id),
        "opponent_balance": ledger.balance(db, opponent.id) if opponent else None,
        "opponent_name": players.display_name(opponent) if opponent else None,
        "offered_to_me": [_reward_out(r) for r in db.scalars(active.where(Reward.created_by != user.id))],
        "offered_by_me": [_reward_out(r) for r in db.scalars(active.where(Reward.created_by == user.id))],
        "costs": list(REWARD_COSTS),
    }


def create(db: Session, user: User, title: str, cost: int) -> Reward:
    if cost not in REWARD_COSTS:
        raise api_error(422, "invalid_cost", "Escolha um dos custos da lista.")
    reward = Reward(created_by=user.id, title=title, cost=cost)
    db.add(reward)
    db.commit()
    return reward


def redeem(db: Session, user: User, reward_id: int) -> Redemption:
    """Pay for a reward offered by the duo. Never lets the balance go negative."""
    # Row lock on the user (PostgreSQL) so two redemptions at once cannot both pass the check.
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    reward = db.get(Reward, reward_id)
    if reward is None or not reward.active:
        raise api_error(404, "not_found", "Esse prêmio não está mais na loja.")
    if reward.created_by == user.id:
        raise api_error(403, "own_reward", "Seus prêmios são para sua dupla resgatar.")
    balance = ledger.balance(db, user.id)
    if balance < reward.cost:
        raise api_error(409, "insufficient_balance", f"Saldo insuficiente: faltam {reward.cost - balance} pts.")

    redemption = Redemption(reward_id=reward.id, redeemed_by=user.id, cost=reward.cost)
    db.add(redemption)
    db.flush()
    ledger.add(db, user.id, "redemption", -reward.cost, redemption.id)
    db.flush()
    if ledger.balance(db, user.id) < 0:  # belt and braces against concurrent requests
        db.rollback()
        raise api_error(409, "insufficient_balance", "Saldo insuficiente para esse resgate.")
    notifications.notify(
        db, reward.created_by, "reward_redeemed",
        f"{players.display_name(user)} resgatou “{reward.title}”. Veja em Prêmios › Para cumprir.",
        {"redemption_id": redemption.id},
    )
    db.commit()
    return redemption


def _get(db: Session, redemption_id: int) -> Redemption:
    redemption = db.get(Redemption, redemption_id)
    if redemption is None:
        raise api_error(404, "not_found", "Resgate não encontrado.")
    return redemption


def fulfill(db: Session, user: User, redemption_id: int) -> None:
    """The reward owner marks it as done."""
    redemption = _get(db, redemption_id)
    if redemption.reward.created_by != user.id:
        raise api_error(403, "not_owner", "Só quem ofereceu o prêmio marca como cumprido.")
    if redemption.status != "pending":
        raise api_error(409, "not_pending", "Esse resgate já foi cumprido.")
    redemption.status = "fulfilled"
    redemption.fulfilled_at = dt.datetime.now(dt.UTC)
    notifications.notify(
        db, redemption.redeemed_by, "reward_fulfilled",
        f"{players.display_name(user)} marcou “{redemption.reward.title}” como cumprido. Confirme em Meus resgates.",
    )
    db.commit()


def receive(db: Session, user: User, redemption_id: int) -> None:
    """Who redeemed confirms they received it (closes the cycle)."""
    redemption = _get(db, redemption_id)
    if redemption.redeemed_by != user.id:
        raise api_error(403, "not_redeemer", "Só quem resgatou confirma o recebimento.")
    if redemption.status == "received":
        raise api_error(409, "already_received", "Esse prêmio já foi marcado como recebido.")
    redemption.status = "received"
    redemption.received_at = dt.datetime.now(dt.UTC)
    if redemption.fulfilled_at is None:
        redemption.fulfilled_at = redemption.received_at
    notifications.notify(
        db, redemption.reward.created_by, "reward_received",
        f"{players.display_name(user)} confirmou que recebeu “{redemption.reward.title}”.",
    )
    db.commit()


def remind(db: Session, user: User, redemption_id: int) -> None:
    redemption = _get(db, redemption_id)
    if redemption.redeemed_by != user.id:
        raise api_error(403, "not_redeemer", "Só quem resgatou pode lembrar.")
    if redemption.status != "pending":
        raise api_error(409, "not_pending", "Esse prêmio já foi cumprido.")
    notifications.notify(
        db, redemption.reward.created_by, "reward_reminder",
        f"{players.display_name(user)} lembrou você de cumprir “{redemption.reward.title}”.",
    )
    db.commit()


def redemptions(db: Session, user: User, scope: str) -> list[dict]:
    """scope "mine": what I redeemed; "to_fulfill": what the duo redeemed from my rewards."""
    stmt = select(Redemption).join(Reward).order_by(Redemption.created_at.desc(), Redemption.id.desc())
    if scope == "mine":
        stmt = stmt.where(Redemption.redeemed_by == user.id)
    else:
        stmt = stmt.where(Reward.created_by == user.id)
    rows = []
    for redemption in db.scalars(stmt):
        owner = db.get(User, redemption.reward.created_by)
        redeemer = db.get(User, redemption.redeemed_by)
        rows.append(
            {
                "id": redemption.id,
                "title": redemption.reward.title,
                "cost": redemption.cost,
                "status": redemption.status,
                "created_at": redemption.created_at,
                "redeemed_on": local_date(redemption.created_at),
                "owner_name": players.display_name(owner),
                "owner_color": players.player_color(db, owner),
                "redeemer_name": players.display_name(redeemer),
                "redeemer_color": players.player_color(db, redeemer),
            }
        )
    return rows


def pending_to_fulfill(db: Session, user: User) -> int:
    stmt = (
        select(func.count())
        .select_from(Redemption)
        .join(Reward)
        .where(Reward.created_by == user.id, Redemption.status == "pending")
    )
    return db.scalar(stmt) or 0
