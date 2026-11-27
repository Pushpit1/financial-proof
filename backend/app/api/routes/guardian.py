"""Runtime Financial Guardian API routes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.application.financial_guardian.runtime import FinancialGuardianRuntime
from app.db.repositories.financial_guardian_audit import (
    SqlAlchemyFinancialGuardianAuditRepository,
)
from app.db.session import get_db
from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation

router = APIRouter(prefix="/guardian", tags=["runtime-guardian"])


class GuardianEvaluateRequest(BaseModel):
    operation: str = Field(..., min_length=1, max_length=100)
    actor_id: str | None = Field(default="operator", max_length=255)
    amount_minor: int = Field(..., ge=0)
    payment_amount_minor: int = Field(default=10000, ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    actor_authorized: bool = True
    operation_authorized: bool = True
    duplicate_detected: bool = False
    state_transition_valid: bool = True
    requires_manual_review: bool = False
    persist_audit: bool = True


class GuardianEvaluateResponse(BaseModel):
    decision: str
    rule: str
    reason: str
    persisted: bool
    audit_id: UUID | None = None
    created_at: datetime | None = None


class GuardianAuditResponse(BaseModel):
    id: UUID
    actor_id: str | None
    operation: str
    rule: str
    decision: str
    reason: str
    created_at: datetime


@router.post(
    "/evaluate",
    response_model=GuardianEvaluateResponse,
    status_code=status.HTTP_200_OK,
)
async def evaluate_guardian(
    request: GuardianEvaluateRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> GuardianEvaluateResponse:
    """Evaluate a financial operation against deterministic Runtime Guardian policies."""
    evaluations: list[GuardianEvaluation] = []

    if not request.actor_authorized or not request.operation_authorized:
        evaluations.append(
            GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule="authorization_guard",
                reason="Actor or operation lacks explicit financial contract authorization.",
            )
        )
    if request.duplicate_detected:
        evaluations.append(
            GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule="duplicate_charge_guard",
                reason="Duplicate operation / idempotency collision detected.",
            )
        )
    if not request.state_transition_valid:
        evaluations.append(
            GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule="invalid_state_transition_guard",
                reason="Requested payment state transition violates the state machine.",
            )
        )
    if (
        request.operation.lower() == "refund"
        and request.amount_minor > request.payment_amount_minor
    ):
        evaluations.append(
            GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule="refund_ceiling_guard",
                reason=(
                    f"Refund amount ({request.amount_minor} minor {request.currency.upper()}) "
                    f"exceeds original payment ({request.payment_amount_minor} minor)."
                ),
            )
        )
    if request.requires_manual_review:
        evaluations.append(
            GuardianEvaluation(
                decision=GuardianDecision.REVIEW,
                rule="manual_review_threshold",
                reason="Operation flagged for secondary review before execution.",
            )
        )
    if not evaluations:
        evaluations.append(
            GuardianEvaluation(
                decision=GuardianDecision.ALLOW,
                rule="guardian_all_checks_passed",
                reason=(
                    f"Operation '{request.operation}' ({request.amount_minor} minor "
                    f"{request.currency.upper()}) satisfied all runtime guards."
                ),
            )
        )

    repo = (
        SqlAlchemyFinancialGuardianAuditRepository(db)
        if request.persist_audit
        else None
    )
    runtime = FinancialGuardianRuntime(audit_repository=repo)
    result = runtime.decide(
        evaluations,
        operation=request.operation,
        actor_id=request.actor_id,
    )

    audit_id: UUID | None = None
    created_at: datetime | None = None
    persisted = False

    if repo is not None:
        db.commit()
        latest = repo.list_all(limit=1)
        if latest:
            audit_id = latest[0].id
            created_at = latest[0].created_at
        persisted = True

    return GuardianEvaluateResponse(
        decision=result.decision.value,
        rule=result.rule,
        reason=result.reason,
        persisted=persisted,
        audit_id=audit_id,
        created_at=created_at,
    )


@router.get("/audit", response_model=list[GuardianAuditResponse])
async def list_guardian_audit(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),  # noqa: B008
) -> list[GuardianAuditResponse]:
    """List persisted immutable Runtime Guardian audit records."""
    repo = SqlAlchemyFinancialGuardianAuditRepository(db)
    records = repo.list_all(limit=limit, offset=offset)
    return [
        GuardianAuditResponse(
            id=record.id,
            actor_id=record.actor_id,
            operation=record.operation,
            rule=record.rule,
            decision=record.decision.value,
            reason=record.reason,
            created_at=record.created_at,
        )
        for record in records
    ]
