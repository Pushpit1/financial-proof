from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

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


def test_decision_service_delegates_to_evaluator() -> None:
    evaluator = FakeEvaluator()
    service = FinancialContractDecisionService(
        evaluator=evaluator,  # type: ignore[arg-type]
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
        evaluator=evaluator,  # type: ignore[arg-type]
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
        evaluator=evaluator,  # type: ignore[arg-type]
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
