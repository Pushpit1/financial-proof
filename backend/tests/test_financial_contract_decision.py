from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.application.services.financial_contract_decision import (
    FinancialContractDecisionService,
)
from app.domain.models.financial import (
    FinancialContract,
    FinancialContractDecision,
)
from app.domain.services.contract_evaluation import (
    ContractEvaluationResult,
    ContractViolation,
)
from app.domain.services.contract_evaluator import ContractEvaluator


class FakeEvaluator:
    def __init__(
        self,
        result: ContractEvaluationResult | None = None,
    ) -> None:
        self.called = False
        self.result = result

    def evaluate(
        self,
        contract: FinancialContract,
        context: Mapping[str, Any] | None = None,
    ) -> ContractEvaluationResult:
        self.called = True

        if self.result is not None:
            return self.result

        return ContractEvaluationResult(
            contract_id=contract.id,
            passed=True,
        )


class FakeDecisionRepository:
    def __init__(self) -> None:
        self.items = []

    def save(self, decision) -> None:
        self.items.append(decision)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.decisions = FakeDecisionRepository()
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if exc_type is None:
            self.committed = True
        else:
            self.rolled_back = True


def test_decision_service_delegates_to_evaluator() -> None:
    evaluator = FakeEvaluator()
    service = FinancialContractDecisionService(
        evaluator=evaluator,
    )

    contract = FinancialContract(
        name="Decision Contract",
    )

    decision = service.evaluate(
        contract,
        {"actor": "underwriter"},
    )

    assert evaluator.called is True
    assert isinstance(decision, FinancialContractDecision)
    assert decision.contract_id == contract.id
    assert decision.passed is True


def test_decision_service_converts_failed_evaluation() -> None:
    contract = FinancialContract(
        name="Failed Decision Contract",
    )

    violation = ContractViolation(
        rule="authorization",
        message="Authorization requirement was not satisfied.",
        field="actor",
        reason_code="authorization_failed",
    )

    evaluator = FakeEvaluator(
        result=ContractEvaluationResult(
            contract_id=contract.id,
            passed=False,
            violations=(violation,),
        )
    )

    service = FinancialContractDecisionService(
        evaluator=evaluator,
    )

    decision = service.evaluate(contract)

    assert decision.passed is False
    assert decision.violation_count == 1
    assert decision.reason_codes == (
        "authorization_failed",
    )


def test_decision_service_preserves_evaluation_timestamp() -> None:
    contract = FinancialContract(
        name="Timestamp Contract",
    )

    evaluated_at = datetime(
        2026,
        8,
        31,
        20,
        0,
        tzinfo=UTC,
    )

    evaluator = FakeEvaluator(
        result=ContractEvaluationResult(
            contract_id=contract.id,
            passed=True,
            evaluated_at=evaluated_at,
        )
    )

    service = FinancialContractDecisionService(
        evaluator=evaluator,
    )

    decision = service.evaluate(contract)

    assert decision.evaluated_at == evaluated_at


def test_decision_service_uses_real_evaluator() -> None:
    service = FinancialContractDecisionService(
        evaluator=ContractEvaluator(),
    )

    contract = FinancialContract(
        name="Valid Decision Contract",
    )

    decision = service.evaluate(contract)

    assert isinstance(decision, FinancialContractDecision)
    assert decision.contract_id == contract.id
    assert decision.passed is True


def test_decision_service_returns_zero_violations_for_success() -> None:
    service = FinancialContractDecisionService()

    contract = FinancialContract(
        name="Successful Decision Contract",
    )

    decision = service.evaluate(contract)

    assert decision.passed is True
    assert decision.violation_count == 0
    assert decision.reason_codes == ()


def test_decision_service_persists_through_unit_of_work() -> None:
    evaluator = FakeEvaluator()
    unit_of_work = FakeUnitOfWork()

    service = FinancialContractDecisionService(
        evaluator=evaluator,
        unit_of_work=unit_of_work,  # type: ignore[arg-type]
    )

    contract = FinancialContract(
        name="Transactional Decision Contract",
    )

    decision = service.evaluate(
        contract,
        persist=True,
    )

    assert decision.contract_id == contract.id
    assert len(unit_of_work.decisions.items) == 1
    assert unit_of_work.decisions.items[0].id == decision.id
    assert unit_of_work.committed is True
    assert unit_of_work.rolled_back is False


def test_decision_service_rejects_persistence_without_unit_of_work() -> None:
    service = FinancialContractDecisionService(
        evaluator=FakeEvaluator(),
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


def test_decision_service_lists_decisions_through_repository() -> None:
    contract = FinancialContract(
        name="Decision History Contract",
    )

    first = FinancialContractDecision(
        contract_id=contract.id,
        passed=True,
    )
    second = FinancialContractDecision(
        contract_id=contract.id,
        passed=False,
        reason_codes=("authorization_failed",),
        violation_count=1,
    )

    class HistoryRepository:
        def list_by_contract(self, contract_id):
            assert contract_id == contract.id
            return [first, second]

    service = FinancialContractDecisionService(
        repository=HistoryRepository(),  # type: ignore[arg-type]
    )

    decisions = service.list_decisions(contract.id)

    assert decisions == [first, second]


def test_decision_service_lists_decisions_through_unit_of_work() -> None:
    contract = FinancialContract(
        name="Unit Of Work History Contract",
    )

    decision = FinancialContractDecision(
        contract_id=contract.id,
        passed=True,
    )

    class HistoryRepository:
        def list_by_contract(self, contract_id):
            assert contract_id == contract.id
            return [decision]

    class HistoryUnitOfWork:
        def __init__(self):
            self.decisions = HistoryRepository()

    service = FinancialContractDecisionService(
        unit_of_work=HistoryUnitOfWork(),  # type: ignore[arg-type]
    )

    decisions = service.list_decisions(contract.id)

    assert decisions == [decision]


def test_decision_service_rejects_history_without_repository() -> None:
    service = FinancialContractDecisionService(
        evaluator=FakeEvaluator(),
    )

    contract_id = uuid4()

    with pytest.raises(
        ValueError,
        match="Decision repository is required",
    ):
        service.list_decisions(contract_id)
