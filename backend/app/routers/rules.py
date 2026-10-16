"""Scoring rules: what is in force and the propose → approve flow between the two members."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..clock import get_today
from ..db import get_db
from ..models import User
from ..schemas import RuleProposalIn, RulesStateOut
from ..scoring import Rules
from ..security import get_current_user
from ..services import rules

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=RulesStateOut)
def read_rules(user: User = Depends(get_current_user), db: Session = Depends(get_db), today: dt.date = Depends(get_today)):
    """Rules in force this week, allowed options and the pending proposal (if any)."""
    return rules.rules_state(db, user, today)


@router.post("/proposals", response_model=RulesStateOut, status_code=status.HTTP_201_CREATED)
def propose(
    data: RuleProposalIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
):
    """Propose new rules. They only take effect after the other member approves."""
    rules.propose(db, user, Rules(**data.model_dump()), today)
    return rules.rules_state(db, user, today)


@router.post("/proposals/{proposal_id}/approve", response_model=RulesStateOut)
def approve(
    proposal_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
):
    """Approve the other member's proposal: new rules from this week on, with this week's points recalculated."""
    rules.approve(db, user, proposal_id, today)
    return rules.rules_state(db, user, today)


@router.post("/proposals/{proposal_id}/reject", response_model=RulesStateOut)
def reject(
    proposal_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    today: dt.date = Depends(get_today),
):
    """Turn down the other member's proposal; the current rules stay."""
    rules.reject(db, user, proposal_id)
    return rules.rules_state(db, user, today)


@router.delete("/proposals/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel(proposal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Withdraw your own pending proposal."""
    rules.cancel(db, user, proposal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
