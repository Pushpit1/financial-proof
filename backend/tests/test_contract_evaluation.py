from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.services.contract_evaluation import (
    ContractEvaluationResult,
    ContractViolation,
)


def test_contract_violation_is_immutable() -> None:
    violation = ContractViolation(
        rule="income_minimum",
        message="Income is below minimum.",
        field="monthly_income",
    )

    with pytest.raises(AttributeError):
        violation.message = "changed"  # type: ignore[misc]


def test_contract_violation_supports_field() -> None:
    violation = ContractViolation(
        rule="income_minimum",
        message="Income is below minimum.",
        field="monthly_income",
    )

    assert violation.rule == "income_minimum"
    assert violation.message == "Income is below minimum."
    assert violation.field == "monthly_income"


def test_contract_violation_allows_missing_field() -> None:
    violation = ContractViolation(
        rule="authorization",
        message="Actor is not authorized.",
    )

    assert violation.field is None


def test_contract_violation_rejects_empty_rule() -> None:
    with pytest.raises(
        ValueError,
        match="Contract violation rule cannot be empty",
    ):
        ContractViolation(
            rule="",
            message="Invalid contract.",
        )


def test_contract_violation_rejects_empty_message() -> None:
    with pytest.raises(
        ValueError,
        match="Contract violation message cannot be empty",
    ):
        ContractViolation(
            rule="income",
            message="",
        )


def test_contract_violation_rejects_empty_field() -> None:
    with pytest.raises(
        ValueError,
        match="Contract violation field cannot be empty",
    ):
        ContractViolation(
            rule="income",
            message="Invalid income.",
            field=" ",
        )


def test_each_violation_gets_unique_id() -> None:
    first = ContractViolation(
        rule="income",
        message="Invalid income.",
    )
    second = ContractViolation(
        rule="income",
        message="Invalid income.",
    )

    assert first.id != second.id


def test_passed_evaluation_has_no_violations() -> None:
    contract_id = uuid4()

    result = ContractEvaluationResult(
        contract_id=contract_id,
        passed=True,
    )

    assert result.contract_id == contract_id
    assert result.passed is True
    assert result.violations == ()
    assert result.violation_count == 0


def test_failed_evaluation_contains_violations() -> None:
    contract_id = uuid4()

    violations = (
        ContractViolation(
            rule="income_minimum",
            message="Income is below minimum.",
            field="monthly_income",
        ),
        ContractViolation(
            rule="authorization",
            message="Actor is not authorized.",
        ),
    )

    result = ContractEvaluationResult(
        contract_id=contract_id,
        passed=False,
        violations=violations,
    )

    assert result.passed is False
    assert result.violations == violations
    assert result.violation_count == 2


def test_evaluation_result_is_immutable() -> None:
    result = ContractEvaluationResult(
        contract_id=uuid4(),
        passed=True,
    )

    with pytest.raises(AttributeError):
        result.passed = False  # type: ignore[misc]


def test_evaluation_result_uses_supplied_timestamp() -> None:
    timestamp = datetime(
        2026,
        8,
        30,
        20,
        0,
        tzinfo=UTC,
    )

    result = ContractEvaluationResult(
        contract_id=uuid4(),
        passed=True,
        evaluated_at=timestamp,
    )

    assert result.evaluated_at == timestamp


def test_evaluation_result_violations_are_immutable_collection() -> None:
    result = ContractEvaluationResult(
        contract_id=uuid4(),
        passed=False,
        violations=(
            ContractViolation(
                rule="income",
                message="Invalid income.",
            ),
        ),
    )

    assert isinstance(result.violations, tuple)
