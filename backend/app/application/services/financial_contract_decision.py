from collections.abc import Mapping
from typing import Any

from app.application.ports.financial_contract_decision import (
    FinancialContractDecisionRepository,
)
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
        repository: FinancialContractDecisionRepository | None = None,
    ) -> None:
        self._evaluator = evaluator or ContractEvaluator()
        self._repository = repository

    def evaluate(
        self,
        contract: FinancialContract,
        context: Mapping[str, Any] | None = None,
        *,
        persist: bool = False,
    ) -> FinancialContractDecision:
        """Evaluate, construct, and optionally persist a decision."""

        result = self._evaluator.evaluate(
            contract=contract,
            context=context,
        )

        decision = FinancialContractDecision(
            contract_id=result.contract_id,
            passed=result.passed,
            reason_codes=result.reason_codes,
            violation_count=result.violation_count,
            evaluated_at=result.evaluated_at,
        )

        if persist:
            if self._repository is None:
                raise ValueError(
                    "Decision repository is required when persist is enabled."
                )

            return self._repository.save(decision)

        return decision
