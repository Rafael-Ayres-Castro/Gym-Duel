"""Scoring rules in force and the two-person approval flow for changing them.

A change starts as a proposal; the current rules stay in force until the other
member approves. Approving creates a new rules version starting this week and
recalculates the points of this week's workouts. Closed weeks are untouched.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import scoring
from ..errors import api_error
from ..models import RuleProposal, ScoringRules, User, Workout
from ..scoring import DEFAULT_RULES, Rules
from . import notifications, players

RULE_FIELDS = tuple(scoring.RULE_OPTIONS)


def _rules_of(row: ScoringRules | RuleProposal) -> Rules:
    return Rules(**{field: getattr(row, field) for field in RULE_FIELDS})


def rules_for_week(db: Session, week_start: dt.date) -> Rules:
    """Rules of the latest version that starts on or before the given week."""
    stmt = (
        select(ScoringRules)
        .where(ScoringRules.effective_from <= week_start)
        .order_by(ScoringRules.effective_from.desc(), ScoringRules.id.desc())
        .limit(1)
    )
    row = db.scalar(stmt)
    return _rules_of(row) if row else DEFAULT_RULES


def rules_for_date(db: Session, day: dt.date) -> Rules:
    return rules_for_week(db, scoring.week_bounds(day)[0])


def workout_points(workout: Workout, rules: Rules) -> int:
    return scoring.calc_points(workout.duration_min, workout.intensity, bool(workout.photo_key), rules)


def pending_proposal(db: Session) -> RuleProposal | None:
    return db.scalar(select(RuleProposal).where(RuleProposal.status == "pending").order_by(RuleProposal.id.desc()))


def _get_pending(db: Session, proposal_id: int) -> RuleProposal:
    proposal = db.get(RuleProposal, proposal_id)
    if proposal is None:
        raise api_error(404, "not_found", "Proposta não encontrada.")
    if proposal.status != "pending":
        raise api_error(409, "already_decided", "Essa proposta já foi decidida.")
    return proposal


def _close(proposal: RuleProposal, status: str, user: User) -> None:
    proposal.status = status
    proposal.decided_by = user.id
    proposal.decided_at = dt.datetime.now(dt.UTC)


def propose(db: Session, user: User, rules: Rules, today: dt.date) -> RuleProposal:
    opponent = players.opponent_of(db, user)
    if opponent is None:
        raise api_error(409, "no_duo", "Sua dupla precisa estar cadastrada para vocês mudarem as regras.")
    if pending_proposal(db):
        raise api_error(409, "proposal_pending", "Já existe uma proposta aguardando aprovação.")
    if rules == rules_for_date(db, today):
        raise api_error(422, "no_change", "A proposta é igual às regras em vigor.")

    proposal = RuleProposal(proposed_by=user.id, **rules.as_dict())
    db.add(proposal)
    db.flush()
    notifications.notify(
        db, opponent.id, "rules_proposed",
        f"{players.display_name(user)} propôs mudar as regras de pontos. Veja em Metas e regras.",
        {"proposal_id": proposal.id},
    )
    db.commit()
    return proposal


def recalculate_week(db: Session, week_start: dt.date, rules: Rules) -> None:
    """Re-apply the formula to the workouts of the week in course (and nothing before it)."""
    for workout in db.scalars(select(Workout).where(Workout.date >= week_start)):
        workout.points = workout_points(workout, rules)


def approve(db: Session, user: User, proposal_id: int, today: dt.date) -> None:
    proposal = _get_pending(db, proposal_id)
    if proposal.proposed_by == user.id:
        raise api_error(403, "own_proposal", "Quem propôs a mudança não pode aprová-la. Espere sua dupla.")
    week_start = scoring.week_bounds(today)[0]
    new_rules = _rules_of(proposal)
    db.add(ScoringRules(**new_rules.as_dict(), effective_from=week_start, proposal_id=proposal.id))
    _close(proposal, "approved", user)
    recalculate_week(db, week_start, new_rules)
    notifications.notify(
        db, proposal.proposed_by, "rules_approved",
        f"{players.display_name(user)} aprovou as novas regras. Os pontos da semana foram recalculados.",
    )
    db.commit()


def reject(db: Session, user: User, proposal_id: int) -> None:
    proposal = _get_pending(db, proposal_id)
    if proposal.proposed_by == user.id:
        raise api_error(403, "own_proposal", "Para desistir da sua proposta, use Cancelar proposta.")
    _close(proposal, "rejected", user)
    notifications.notify(
        db, proposal.proposed_by, "rules_rejected",
        f"{players.display_name(user)} recusou a proposta de mudar as regras. As regras atuais continuam valendo.",
    )
    db.commit()


def cancel(db: Session, user: User, proposal_id: int) -> None:
    proposal = _get_pending(db, proposal_id)
    if proposal.proposed_by != user.id:
        raise api_error(403, "not_author", "Só quem propôs pode cancelar a proposta.")
    _close(proposal, "cancelled", user)
    db.commit()


def proposal_out(db: Session, proposal: RuleProposal | None, viewer: User) -> dict | None:
    if proposal is None:
        return None
    author = db.get(User, proposal.proposed_by)
    return {
        "id": proposal.id,
        "proposed_by_me": proposal.proposed_by == viewer.id,
        "proposed_by_name": players.display_name(author),
        "values": _rules_of(proposal).as_dict(),
        "created_at": proposal.created_at,
    }


def rules_state(db: Session, viewer: User, today: dt.date) -> dict:
    return {
        "current": rules_for_date(db, today).as_dict(),
        "options": {field: list(values) for field, values in scoring.RULE_OPTIONS.items()},
        "pending": proposal_out(db, pending_proposal(db), viewer),
    }
