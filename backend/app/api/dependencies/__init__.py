"""Dependency providers for API routes."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.core.config import get_settings
from app.db.session import get_db
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.services.proof_evaluator import (
    ProofEvaluationPolicy,
    ProofEvaluator,
)


def get_financial_proof_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> FinancialProofApplicationService:
    """Build the financial proof application service."""
    settings = get_settings()

    policy = ProofEvaluationPolicy(
        minimum_ready_confidence=settings.proof_minimum_ready_confidence,
        minimum_supported_claim_ratio=(
            settings.proof_minimum_supported_claim_ratio
        ),
    )

    return FinancialProofApplicationService(
        FinancialUnitOfWork(db),
        evaluator=ProofEvaluator(policy),
    )

