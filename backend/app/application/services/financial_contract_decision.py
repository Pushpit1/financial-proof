from collections.abc import Mapping
from typing import Any

from app.domain.models.financial import FinancialContract
from app.domain.services.contract_evaluation import (
    ContractEvaluationResult,
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
    ) -> ContractEvaluationResult:
        """Evaluate a financial contract against supplied context."""
        return self._evaluator.evaluate(
            contract=contract,
            context=context,
        )
