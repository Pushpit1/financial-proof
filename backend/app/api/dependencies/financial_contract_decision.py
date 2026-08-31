"""Dependency providers for financial contract decisions."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.services.financial_contract_decision import (
    FinancialContractDecisionService,
)
from app.db.session import get_db
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.services.contract_evaluator import ContractEvaluator


def get_financial_contract_decision_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> FinancialContractDecisionService:
    """Build the financial contract decision service."""
    return FinancialContractDecisionService(
        evaluator=ContractEvaluator(),
        unit_of_work=FinancialUnitOfWork(db),
    )
