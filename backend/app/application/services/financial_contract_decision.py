"""Application service for financial contract decisions."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from app.application.ports.unit_of_work import FinancialUnitOfWorkPort
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
        unit_of_work: FinancialUnitOfWorkPort | None = None,
    ) -> None:
        self._evaluator = evaluator or ContractEvaluator()
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

        return decision

    def list_decisions(
        self,
        contract_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FinancialContractDecision]:
        """Return a page of persisted decisions for a contract."""
        if self._unit_of_work is None:
            raise ValueError("Decision unit of work is required")

        if limit < 1:
            raise ValueError("Decision history limit must be at least 1.")

        if limit > 100:
            raise ValueError("Decision history limit cannot exceed 100.")

        if offset < 0:
            raise ValueError("Decision history offset cannot be negative.")

        return self._unit_of_work.decisions.list_by_contract(
            contract_id,
            limit=limit,
            offset=offset,
        )
