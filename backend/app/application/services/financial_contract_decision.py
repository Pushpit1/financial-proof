"""Application service for financial contract decisions."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from app.application.ports.financial_contract_decision import (
    FinancialContractDecisionRepository,
)
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.models.financial import (
    FinancialContract,
    FinancialContractDecision,
)
from app.domain.services.contract_evaluator import ContractEvaluator


class FinancialContractDecisionService:
    """Coordinate financial contract evaluation and decision persistence."""

    def __init__(
        self,
        evaluator: ContractEvaluator | None = None,
        repository: FinancialContractDecisionRepository | None = None,
        unit_of_work: FinancialUnitOfWork | None = None,
    ) -> None:
        self._evaluator = evaluator or ContractEvaluator()
        self._repository = repository
        self._unit_of_work = unit_of_work

    def evaluate(
        self,
        contract: FinancialContract,
        context: Mapping[str, Any] | None = None,
        *,
        persist: bool = False,
    ) -> FinancialContractDecision:
        """Evaluate a contract and optionally persist its decision."""
        if persist and self._unit_of_work is None:
            raise ValueError("Decision unit of work is required")

        result = self._evaluator.evaluate(
            contract,
            context,
        )

        decision = FinancialContractDecision(
            contract_id=contract.id,
            passed=result.passed,
            reason_codes=tuple(
                violation.reason_code
                for violation in result.violations
            ),
            violation_count=len(result.violations),
            evaluated_at=result.evaluated_at,
        )

        if persist:
            if self._unit_of_work is None:
                raise ValueError("Decision unit of work is required")

            with self._unit_of_work as unit_of_work:
                unit_of_work.decisions.save(decision)

        elif self._repository is not None:
            self._repository.save(decision)

        return decision

    def list_decisions(
        self,
        contract_id: UUID,
    ) -> list[FinancialContractDecision]:
        """Return all persisted decisions for a contract."""
        repository = self._repository

        if repository is None and self._unit_of_work is not None:
            repository = self._unit_of_work.decisions

        if repository is None:
            raise ValueError("Decision repository is required")

        return repository.list_by_contract(contract_id)
