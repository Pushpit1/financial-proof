from decimal import Decimal

import pytest

from app.domain.enums.financial import (
    ClaimType,
    ContractOperator,
)
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import (
    ConfidenceScore,
    ContractField,
    FinancialConstraint,
)


def test_financial_constraint_supports_numeric_comparison() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN_OR_EQUAL,
        value=Decimal("50000"),
        currency="inr",
    )

    assert constraint.field == "monthly_income"
    assert constraint.operator == ContractOperator.GREATER_THAN_OR_EQUAL
    assert constraint.value == Decimal("50000")
    assert constraint.currency == "INR"


def test_financial_constraint_normalizes_currency() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN,
        value=Decimal("50000"),
        currency="usd",
    )

    assert constraint.currency == "USD"


def test_financial_constraint_is_immutable() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN,
        value=Decimal("50000"),
    )

    with pytest.raises(AttributeError):
        constraint.value = Decimal("100000")  # type: ignore[misc]


def test_financial_constraint_has_unique_ids() -> None:
    first = FinancialConstraint(
        field="income",
        operator=ContractOperator.GREATER_THAN,
        value=Decimal("0"),
    )
    second = FinancialConstraint(
        field="expense",
        operator=ContractOperator.LESS_THAN,
        value=Decimal("10000"),
    )

    assert first.id != second.id


def test_financial_constraint_rejects_empty_field() -> None:
    with pytest.raises(
        ValueError,
        match="Financial constraint field cannot be empty",
    ):
        FinancialConstraint(
            field="",
            operator=ContractOperator.GREATER_THAN,
            value=Decimal("0"),
        )


def test_financial_constraint_rejects_surrounding_field_whitespace() -> None:
    with pytest.raises(
        ValueError,
        match="Financial constraint field cannot contain surrounding whitespace",
    ):
        FinancialConstraint(
            field=" income ",
            operator=ContractOperator.GREATER_THAN,
            value=Decimal("0"),
        )


@pytest.mark.parametrize(
    "operator",
    [
        ContractOperator.EXISTS,
        ContractOperator.NOT_EXISTS,
        ContractOperator.IN,
        ContractOperator.NOT_IN,
    ],
)
def test_financial_constraint_rejects_non_numeric_operators(
    operator: ContractOperator,
) -> None:
    with pytest.raises(
        ValueError,
        match="Financial constraints require a numeric comparison operator",
    ):
        FinancialConstraint(
            field="income",
            operator=operator,
            value=Decimal("0"),
        )


def test_financial_constraint_rejects_invalid_currency() -> None:
    with pytest.raises(
        ValueError,
        match="Financial constraint currency must be a 3-letter ISO code",
    ):
        FinancialConstraint(
            field="income",
            operator=ContractOperator.GREATER_THAN,
            value=Decimal("0"),
            currency="IN",
        )


def test_financial_constraint_rejects_non_letter_currency() -> None:
    with pytest.raises(
        ValueError,
        match="Financial constraint currency must contain only letters",
    ):
        FinancialConstraint(
            field="income",
            operator=ContractOperator.GREATER_THAN,
            value=Decimal("0"),
            currency="12A",
        )


def test_contract_supports_financial_constraints() -> None:
    income = ContractField(
        name="monthly_income",
        data_type="money",
    )

    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN_OR_EQUAL,
        value=Decimal("50000"),
        currency="INR",
    )

    contract = FinancialContract(
        name="Income Contract",
        inputs=(income,),
        financial_constraints=(constraint,),
    )

    assert contract.financial_constraints == (constraint,)


def test_contract_rejects_duplicate_financial_constraints() -> None:
    income = ContractField(
        name="monthly_income",
        data_type="money",
    )

    first = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN,
        value=Decimal("50000"),
    )
    second = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN,
        value=Decimal("60000"),
    )

    with pytest.raises(
        ValueError,
        match="Duplicate financial constraint",
    ):
        FinancialContract(
            name="Duplicate Constraint Contract",
            inputs=(income,),
            financial_constraints=(first, second),
        )


def test_contract_rejects_constraint_for_undeclared_field() -> None:
    constraint = FinancialConstraint(
        field="monthly_income",
        operator=ContractOperator.GREATER_THAN,
        value=Decimal("50000"),
    )

    with pytest.raises(
        ValueError,
        match="Financial constraint field must reference a declared contract field",
    ):
        FinancialContract(
            name="Invalid Constraint Contract",
            inputs=(
                ContractField(
                    name="monthly_expense",
                    data_type="money",
                ),
            ),
            financial_constraints=(constraint,),
        )


def test_existing_contract_claim_types_still_work() -> None:
    contract = FinancialContract(
        name="Income Verification",
        required_claim_types=(
            ClaimType.INCOME,
            ClaimType.EMPLOYMENT,
        ),
        minimum_confidence=ConfidenceScore(
            Decimal("0.80")
        ),
    )

    assert contract.required_claim_types == (
        ClaimType.INCOME,
        ClaimType.EMPLOYMENT,
    )
