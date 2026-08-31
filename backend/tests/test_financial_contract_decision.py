from collections.abc import Mapping
from typing import Any

from app.domain.models.financial import FinancialContract
from app.domain.services.contract_evaluation import (
    ContractEvaluationResult,
)
from app.domain.services.contract_evaluator import ContractEvaluator
from app.application.services.financial_contract_decision import (
    FinancialContractDecisionService,
)


class FakeEvaluator:
    def __init__(self) -> None:
        self.called = False

    def evaluate(
        self,
        contract: FinancialContract,
        context: Mapping[str, Any] | None = None,
    ) -> ContractEvaluationResult:
        self.called = True

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

    result = service.evaluate(
        contract,
        {"actor": "underwriter"},
    )

    assert evaluator.called is True
    assert result.contract_id == contract.id
    assert result.passed is True


def test_decision_service_uses_real_evaluator() -> None:
    service = FinancialContractDecisionService(
        evaluator=ContractEvaluator(),
    )

    contract = FinancialContract(
        name="Valid Decision Contract",
    )

    result = service.evaluate(contract)

    assert result.contract_id == contract.id
    assert result.passed is True


def test_decision_service_preserves_evaluation_result() -> None:
    evaluator = FakeEvaluator()
    service = FinancialContractDecisionService(
        evaluator=evaluator,  # type: ignore[arg-type]
    )

    contract = FinancialContract(
        name="Result Contract",
    )

    result = service.evaluate(contract)

    assert isinstance(result, ContractEvaluationResult)
    assert result.violations == ()
    assert result.reason_codes == ()
