from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.models.financial import FinancialContractDecision


def test_decision_supports_passed_contract() -> None:
    contract_id = uuid4()

    decision = FinancialContractDecision(
        contract_id=contract_id,
        passed=True,
    )

    assert decision.contract_id == contract_id
    assert decision.passed is True
    assert decision.reason_codes == ()
    assert decision.violation_count == 0


def test_decision_supports_failed_contract() -> None:
    decision = FinancialContractDecision(
        contract_id=uuid4(),
        passed=False,
        reason_codes=(
            "authorization_failed",
            "financial_constraint_failed",
        ),
        violation_count=2,
    )

    assert decision.passed is False
    assert decision.violation_count == 2
    assert decision.reason_codes == (
        "authorization_failed",
        "financial_constraint_failed",
    )


def test_decision_is_immutable() -> None:
    decision = FinancialContractDecision(
        contract_id=uuid4(),
        passed=True,
    )

    with pytest.raises(AttributeError):
        decision.passed = False  # type: ignore[misc]


def test_decision_rejects_negative_violation_count() -> None:
    with pytest.raises(
        ValueError,
        match="Decision violation count cannot be negative",
    ):
        FinancialContractDecision(
            contract_id=uuid4(),
            passed=False,
            violation_count=-1,
        )


def test_decision_requires_matching_violation_count() -> None:
    with pytest.raises(
        ValueError,
        match="Decision violation count must match reason codes",
    ):
        FinancialContractDecision(
            contract_id=uuid4(),
            passed=False,
            reason_codes=("authorization_failed",),
            violation_count=2,
        )


def test_decision_preserves_timestamp() -> None:
    timestamp = datetime(
        2026,
        8,
        31,
        20,
        0,
        tzinfo=UTC,
    )

    decision = FinancialContractDecision(
        contract_id=uuid4(),
        passed=True,
        evaluated_at=timestamp,
    )

    assert decision.evaluated_at == timestamp


def test_decision_generates_unique_ids() -> None:
    first = FinancialContractDecision(
        contract_id=uuid4(),
        passed=True,
    )
    second = FinancialContractDecision(
        contract_id=uuid4(),
        passed=True,
    )

    assert first.id != second.id
