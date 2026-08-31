from collections.abc import Mapping
from typing import Any

from app.domain.models.financial import (
    FinancialContract,
    FinancialContractDecision,
)
from app.domain.services.contract_evaluator import ContractEvaluator


class FinancialContractDecisionService:
    """Application service for deterministic contract decisions."""

    def __init__(
        self,
        evaluator: ContractEvaluator | None = None,
    ) -> None:
        self._evaluator = evaluator or ContractEvaluator()

    def evaluate(
        self,
        contract: FinancialContract,
        context: Mapping[str, Any] | None = None,
    ) -> FinancialContractDecision:
        """Evaluate a contract and return a decision record."""
        result = self._evaluator.evaluate(
            contract=contract,
            context=context,
        )

        return FinancialContractDecision(
            contract_id=result.contract_id,
            passed=result.passed,
            reason_codes=result.reason_codes,
            violation_count=result.violation_count,
            evaluated_at=result.evaluated_at,
        )
