"""Application-service dependencies."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.db.session import get_db
from app.db.unit_of_work import FinancialUnitOfWork


def get_financial_proof_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> FinancialProofApplicationService:
    """Build the financial proof application service."""
    return FinancialProofApplicationService(
        FinancialUnitOfWork(db)
    )
