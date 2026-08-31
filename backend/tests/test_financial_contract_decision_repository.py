from collections.abc import Mapping
from typing import Any
from uuid import UUID

import pytest

from app.application.ports.financial_contract_decision import (
    FinancialContractDecisionRepository,
)
from app.application.services.financial_contract_decision import (
    FinancialContractDecisionService,
)
from app.domain.models.financial import (
    FinancialContract,
    FinancialContractDecision,
)


class InMemoryDecisionRepository(
    FinancialContractDecisionRepository,
):
    def __init__(self) -> None:
        self.items: dict[
            UUID,
            FinancialContractDecision,
        ] = {}

    def save(
        self,
        decision: FinancialContractDecision,
    ) -> FinancialContractDecision:
        self.items[decision.id] = decision
        return decision

    def get_by_id(
        self,
        decision_id: UUID,
    ) -> FinancialContractDecision | None:
        return self.items.get(decision_id)


class FakeEvaluator:
    def evaluate(
        self,
        contract: FinancialContract,
        context: Mapping[str, Any] | None = None,
    ):
        from app.domain.services.contract_evaluation import (
            ContractEvaluationResult,
        )

        return ContractEvaluationResult(
            contract_id=contract.id,
            passed=True,
        )


def test_repository_can_save_and_get_decision() -> None:
    repository = InMemoryDecisionRepository()

    decision = FinancialContractDecision(
        contract_id=UUID("11111111-1111-1111-1111-111111111111"),
        passed=True,
    )

    saved = repository.save(decision)

    assert saved == decision
    assert repository.get_by_id(decision.id) == decision


def test_service_persists_when_requested() -> None:
    repository = InMemoryDecisionRepository()

    service = FinancialContractDecisionService(
        evaluator=FakeEvaluator(),  # type: ignore[arg-type]
        repository=repository,
    )

    contract = FinancialContract(
        name="Persisted Contract",
    )

    decision = service.evaluate(
        contract,
        persist=True,
    )

    assert decision.passed is True
    assert repository.get_by_id(decision.id) == decision


def test_service_does_not_require_repository_by_default() -> None:
    service = FinancialContractDecisionService(
        evaluator=FakeEvaluator(),  # type: ignore[arg-type]
    )

    contract = FinancialContract(
        name="Non Persisted Contract",
    )

    decision = service.evaluate(contract)

    assert decision.passed is True


def test_service_rejects_persistence_without_repository() -> None:
    service = FinancialContractDecisionService(
        evaluator=FakeEvaluator(),  # type: ignore[arg-type]
    )

    contract = FinancialContract(
        name="Missing Repository Contract",
    )

    with pytest.raises(
        ValueError,
        match="Decision repository is required",
    ):
        service.evaluate(
            contract,
            persist=True,
        )
