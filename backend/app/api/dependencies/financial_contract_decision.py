"""Dependency providers for financial contract decisions."""

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import get_financial_unit_of_work
from app.application.ports.unit_of_work import FinancialUnitOfWorkPort
from app.application.services.financial_contract_decision import (
    FinancialContractDecisionService,
)
from app.domain.services.contract_evaluator import ContractEvaluator


def get_financial_contract_decision_service(
    unit_of_work: Annotated[
        FinancialUnitOfWorkPort,
        Depends(get_financial_unit_of_work),
    ],
) -> FinancialContractDecisionService:
    """Build the financial contract decision service."""
    return FinancialContractDecisionService(
        evaluator=ContractEvaluator(),
        unit_of_work=unit_of_work,
    )
