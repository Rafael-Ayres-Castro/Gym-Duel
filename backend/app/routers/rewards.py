"""Rewards store, redemptions and their cycle (pending → fulfilled → received)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import RedeemOut, RedemptionOut, RewardIn, RewardOut, StoreOut
from ..security import get_current_user
from ..services import ledger, rewards

router = APIRouter(tags=["rewards"])
NO_CONTENT = status.HTTP_204_NO_CONTENT


@router.get("/rewards", response_model=StoreOut)
def read_store(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Both balances and the rewards on each side of the store."""
    return rewards.store(db, user)


@router.post("/rewards", response_model=RewardOut, status_code=status.HTTP_201_CREATED)
def create_reward(data: RewardIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Offer something you are happy to do; your duo redeems it with their points."""
    reward = rewards.create(db, user, data.title, data.cost)
    return {"id": reward.id, "title": reward.title, "cost": reward.cost, "created_by": reward.created_by}


@router.post("/rewards/{reward_id}/redeem", response_model=RedeemOut, status_code=status.HTTP_201_CREATED)
def redeem(reward_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Redeem a reward offered by your duo. Fails (409) without enough balance."""
    redemption = rewards.redeem(db, user, reward_id)
    return {"redemption_id": redemption.id, "balance": ledger.balance(db, user.id)}


@router.get("/redemptions", response_model=list[RedemptionOut])
def list_redemptions(
    scope: Literal["mine", "to_fulfill"] = Query("mine", description="mine (meus resgates) ou to_fulfill (para cumprir)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return rewards.redemptions(db, user, scope)


@router.post("/redemptions/{redemption_id}/fulfill", status_code=NO_CONTENT)
def fulfill(redemption_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The reward owner marks it as done."""
    rewards.fulfill(db, user, redemption_id)
    return Response(status_code=NO_CONTENT)


@router.post("/redemptions/{redemption_id}/receive", status_code=NO_CONTENT)
def receive(redemption_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Who redeemed confirms they received it."""
    rewards.receive(db, user, redemption_id)
    return Response(status_code=NO_CONTENT)


@router.post("/redemptions/{redemption_id}/remind", status_code=NO_CONTENT)
def remind(redemption_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Nudge the reward owner about a pending redemption."""
    rewards.remind(db, user, redemption_id)
    return Response(status_code=NO_CONTENT)
