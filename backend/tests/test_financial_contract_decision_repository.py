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
        self.items: dict[UUID, FinancialContractDecision] = {}

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

    def list_by_contract(
        self,
        contract_id: UUID,
    ) -> list[FinancialContractDecision]:
        return [
            decision
            for decision in self.items.values()
            if decision.contract_id == contract_id
        ]


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


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.decisions = InMemoryDecisionRepository()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        return None


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
    unit_of_work = FakeUnitOfWork()

    service = FinancialContractDecisionService(
        evaluator=FakeEvaluator(),
        unit_of_work=unit_of_work,  # type: ignore[arg-type]
    )

    contract = FinancialContract(
        name="Persisted Contract",
    )

    decision = service.evaluate(
        contract,
        persist=True,
    )

    assert decision.passed is True
    assert unit_of_work.decisions.get_by_id(decision.id) == decision


def test_service_does_not_require_unit_of_work_by_default() -> None:
    service = FinancialContractDecisionService(
        evaluator=FakeEvaluator(),  # type: ignore[arg-type]
    )

    contract = FinancialContract(
        name="Non Persisted Contract",
    )

    decision = service.evaluate(contract)

    assert decision.passed is True


def test_service_rejects_persistence_without_unit_of_work() -> None:
    service = FinancialContractDecisionService(
        evaluator=FakeEvaluator(),  # type: ignore[arg-type]
    )

    contract = FinancialContract(
        name="Missing Unit Of Work Contract",
    )

    with pytest.raises(
        ValueError,
        match="Decision unit of work is required",
    ):
        service.evaluate(
            contract,
            persist=True,
        )
