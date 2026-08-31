"""Application service for financial contract decisions."""

from collections.abc import Mapping
from typing import Any

from app.domain.models.financial import (
    FinancialContract,
    FinancialContractDecision,
)
from app.domain.services.contract_evaluator import ContractEvaluator


class FinancialContractDecisionService:
    """Evaluate contracts and optionally persist decisions transactionally."""

    def __init__(
        self,
        evaluator: ContractEvaluator | None = None,
        unit_of_work=None,
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
            context or {},
        )

        decision = FinancialContractDecision(
            contract_id=contract.id,
            passed=result.passed,
            reason_codes=tuple(
                violation.reason_code
                for violation in result.violations
            ),
            violation_count=result.violation_count,
            evaluated_at=result.evaluated_at,
        )

        if persist:
            with self._unit_of_work as unit_of_work:
                unit_of_work.decisions.save(decision)

        return decision
