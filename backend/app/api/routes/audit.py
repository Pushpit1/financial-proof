"""Unified persisted audit trail & authentication status API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import authentication
from app.core.authentication import AuthenticationError
from app.db.models.financial import (
    EvidenceModel,
    FinancialContractDecisionModel,
    ProofEvaluationModel,
)
from app.db.models.financial_guardian_audit import (
    FinancialGuardianAuditRecordModel,
)
from app.db.session import get_db

router = APIRouter(tags=["audit-and-auth"])


class AuditEventOut(BaseModel):
    id: str
    category: str
    action: str
    summary: str
    created_at: str


@router.get("/audit", response_model=list[AuditEventOut])
async def list_audit_trail(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),  # noqa: B008
) -> list[AuditEventOut]:
    """Return a unified timeline of persisted audit events across subsystems."""
    events: list[tuple[datetime, AuditEventOut]] = []

    if category in (None, "", "guardian"):
        guardian_rows = db.scalars(
            select(FinancialGuardianAuditRecordModel)
            .order_by(FinancialGuardianAuditRecordModel.created_at.desc())
            .limit(limit)
        ).all()
        for g in guardian_rows:
            events.append(
                (
                    g.created_at,
                    AuditEventOut(
                        id=str(g.id),
                        category="guardian",
                        action=f"guardian_{g.decision}",
                        summary=f"[{g.operation}] {g.rule}: {g.reason}",
                        created_at=g.created_at.isoformat(),
                    ),
                )
            )

    if category in (None, "", "proof"):
        eval_rows = db.scalars(
            select(ProofEvaluationModel)
            .order_by(ProofEvaluationModel.evaluated_at.desc())
            .limit(limit)
        ).all()
        for ev in eval_rows:
            events.append(
                (
                    ev.evaluated_at,
                    AuditEventOut(
                        id=str(ev.id),
                        category="proof",
                        action=f"proof_evaluated_{ev.status}",
                        summary=(
                            f"Proof {str(ev.proof_id)[:8]} confidence={ev.overall_confidence}"
                        ),
                        created_at=ev.evaluated_at.isoformat(),
                    ),
                )
            )

    if category in (None, "", "contract"):
        decision_rows = db.scalars(
            select(FinancialContractDecisionModel)
            .order_by(FinancialContractDecisionModel.evaluated_at.desc())
            .limit(limit)
        ).all()
        for d in decision_rows:
            events.append(
                (
                    d.evaluated_at,
                    AuditEventOut(
                        id=str(d.id),
                        category="contract",
                        action="contract_decision_" + ("passed" if d.passed else "failed"),
                        summary=(
                            f"Contract {str(d.contract_id)[:8]} violations={d.violation_count}"
                        ),
                        created_at=d.evaluated_at.isoformat(),
                    ),
                )
            )

    if category in (None, "", "evidence"):
        ev_rows = db.scalars(select(EvidenceModel).limit(limit)).all()
        for doc in ev_rows:
            dt = datetime.combine(doc.received_at, datetime.min.time())
            events.append(
                (
                    dt,
                    AuditEventOut(
                        id=str(doc.id),
                        category="evidence",
                        action=f"evidence_{doc.status}",
                        summary=f"{doc.source_name} ({doc.evidence_type}) checksum={doc.checksum}",
                        created_at=doc.received_at.isoformat(),
                    ),
                )
            )

    events.sort(key=lambda item: item[0].isoformat(), reverse=True)
    return [item[1] for item in events[:limit]]


@router.get("/auth/status")
async def auth_status(
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    """Report authentication configuration status and validate Bearer token if sent."""
    cfg = authentication.settings
    token_configured = cfg.api_auth_token is not None and bool(
        cfg.api_auth_token.get_secret_value().strip()
    )

    authenticated = False
    subject: str | None = None
    role: str | None = None

    if token_configured and authorization:
        try:
            principal = authentication.get_authenticator().authenticate(authorization)
            authenticated = True
            subject = principal.subject
            role = principal.role
        except AuthenticationError:
            authenticated = False

    return {
        "auth_configured": token_configured,
        "authenticated": authenticated,
        "subject": subject,
        "role": role,
    }
