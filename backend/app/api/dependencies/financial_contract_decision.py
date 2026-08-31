"""Dependency providers for financial contract decisions."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.ports.financial_contract_decision import (
    FinancialContractDecisionRepository,
)
from app.application.services.financial_contract_decision import (
    FinancialContractDecisionService,
)
from app.db.repositories.financial_contract_decision import (
    SqlAlchemyFinancialContractDecisionRepository,
)
from app.db.session import get_db
from app.domain.services.contract_evaluator import ContractEvaluator


def get_financial_contract_decision_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> FinancialContractDecisionService:
    """Build the financial contract decision service."""
    repository: FinancialContractDecisionRepository = (
        SqlAlchemyFinancialContractDecisionRepository(db)
    )

    return FinancialContractDecisionService(
        evaluator=ContractEvaluator(),
        repository=repository,
    )
