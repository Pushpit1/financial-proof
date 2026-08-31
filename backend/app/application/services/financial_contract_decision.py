from uuid import UUID

from app.application.ports.financial_contract_decision import (
    FinancialContractDecisionRepository,
)
from app.domain.models.financial import (
    FinancialContract,
    FinancialContractDecision,
)
from app.domain.services.contract_evaluator import ContractEvaluator


class FinancialContractDecisionService:
    """Evaluate financial contracts with optional decision persistence."""

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
        context: dict | None = None,
        *,
        persist: bool = False,
    ) -> FinancialContractDecision:
        """Evaluate a contract and optionally persist its decision."""
        if persist and self._repository is None:
            raise ValueError("Decision repository is required")

        result = self._evaluator.evaluate(
            contract,
            context or {},
        )

        reason_codes = tuple(
            violation.reason_code
            for violation in result.violations
        )

        decision = FinancialContractDecision(
            contract_id=contract.id,
            passed=result.passed,
            reason_codes=reason_codes,
            violation_count=result.violation_count,
            evaluated_at=result.evaluated_at,
        )

        if persist:
            return self._repository.save(decision)

        return decision

    def get_by_id(
        self,
        decision_id: UUID,
    ) -> FinancialContractDecision | None:
        """Retrieve a persisted decision."""
        if self._repository is None:
            raise ValueError(
                "A repository is required to retrieve decisions."
            )

        return self._repository.get_by_id(decision_id)

    def list_by_contract(
        self,
        contract_id: UUID,
    ) -> list[FinancialContractDecision]:
        """Retrieve persisted decisions for a contract."""
        if self._repository is None:
            raise ValueError(
                "A repository is required to retrieve decisions."
            )

        return self._repository.list_by_contract(contract_id)
