from decimal import Decimal

import pytest

from app.domain.enums.financial import (
    ClaimType,
    ContractRuleType,
)
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import (
    ConfidenceScore,
    ContractRule,
)


def test_financial_contract_defaults() -> None:
    contract = FinancialContract(
        name="Standard Financial Review",
    )

    assert contract.name == "Standard Financial Review"
    assert contract.version == 1
    assert contract.minimum_confidence == ConfidenceScore(
        Decimal("0")
    )
    assert contract.minimum_supported_claim_ratio == Decimal("1")
    assert contract.required_claim_types == ()
    assert contract.preconditions == ()
    assert contract.invariants == ()
    assert contract.postconditions == ()


def test_financial_contract_supports_required_claim_types() -> None:
    contract = FinancialContract(
        name="Income Verification",
        version=2,
        minimum_confidence=ConfidenceScore(
            Decimal("0.80")
        ),
        minimum_supported_claim_ratio=Decimal("0.90"),
        required_claim_types=(
            ClaimType.INCOME,
            ClaimType.EMPLOYMENT,
        ),
    )

    assert contract.version == 2
    assert contract.minimum_confidence == ConfidenceScore(
        Decimal("0.80")
    )
    assert contract.minimum_supported_claim_ratio == Decimal("0.90")
    assert contract.required_claim_types == (
        ClaimType.INCOME,
        ClaimType.EMPLOYMENT,
    )


def test_financial_contract_rejects_empty_name() -> None:
    with pytest.raises(
        ValueError,
        match="Contract name cannot be empty",
    ):
        FinancialContract(name="")


def test_financial_contract_rejects_whitespace_name() -> None:
    with pytest.raises(
        ValueError,
        match="Contract name cannot be empty",
    ):
        FinancialContract(name="   ")


def test_financial_contract_rejects_invalid_version() -> None:
    with pytest.raises(
        ValueError,
        match="Contract version must be at least 1",
    ):
        FinancialContract(
            name="Invalid Version",
            version=0,
        )


@pytest.mark.parametrize(
    "ratio",
    [
        Decimal("-0.01"),
        Decimal("1.01"),
    ],
)
def test_financial_contract_rejects_invalid_supported_claim_ratio(
    ratio: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="Minimum supported claim ratio must be between 0 and 1",
    ):
        FinancialContract(
            name="Invalid Ratio",
            minimum_supported_claim_ratio=ratio,
        )


def test_financial_contract_is_immutable() -> None:
    contract = FinancialContract(
        name="Immutable Contract",
    )

    with pytest.raises(AttributeError):
        contract.name = "Changed"  # type: ignore[misc]


def test_contract_rule_is_immutable() -> None:
    rule = ContractRule(
        name="Payment exists",
        expression="payment.exists == true",
        rule_type=ContractRuleType.PRECONDITION,
    )

    with pytest.raises(AttributeError):
        rule.name = "Changed"  # type: ignore[misc]


def test_contract_rule_has_unique_ids() -> None:
    first = ContractRule(
        name="First",
        expression="payment.exists == true",
        rule_type=ContractRuleType.PRECONDITION,
    )
    second = ContractRule(
        name="Second",
        expression="payment.amount > 0",
        rule_type=ContractRuleType.INVARIANT,
    )

    assert first.id != second.id


def test_contract_rule_rejects_empty_name() -> None:
    with pytest.raises(
        ValueError,
        match="Contract rule name cannot be empty",
    ):
        ContractRule(
            name="",
            expression="payment.exists == true",
            rule_type=ContractRuleType.PRECONDITION,
        )


def test_contract_rule_rejects_empty_expression() -> None:
    with pytest.raises(
        ValueError,
        match="Contract rule expression cannot be empty",
    ):
        ContractRule(
            name="Payment exists",
            expression=" ",
            rule_type=ContractRuleType.PRECONDITION,
        )


def test_contract_supports_all_rule_types() -> None:
    precondition = ContractRule(
        name="Payment exists",
        expression="payment.exists == true",
        rule_type=ContractRuleType.PRECONDITION,
    )
    invariant = ContractRule(
        name="Payment positive",
        expression="payment.amount > 0",
        rule_type=ContractRuleType.INVARIANT,
    )
    postcondition = ContractRule(
        name="Refund linked",
        expression="refund.original_payment_id != null",
        rule_type=ContractRuleType.POSTCONDITION,
    )

    contract = FinancialContract(
        name="Payment Safety",
        preconditions=(precondition,),
        invariants=(invariant,),
        postconditions=(postcondition,),
    )

    assert contract.preconditions == (precondition,)
    assert contract.invariants == (invariant,)
    assert contract.postconditions == (postcondition,)


def test_contract_rejects_wrong_precondition_rule_type() -> None:
    invariant = ContractRule(
        name="Payment positive",
        expression="payment.amount > 0",
        rule_type=ContractRuleType.INVARIANT,
    )

    with pytest.raises(
        ValueError,
        match="Contract rule must have type 'precondition'",
    ):
        FinancialContract(
            name="Invalid Contract",
            preconditions=(invariant,),
        )


def test_contract_rejects_wrong_invariant_rule_type() -> None:
    postcondition = ContractRule(
        name="Refund linked",
        expression="refund.original_payment_id != null",
        rule_type=ContractRuleType.POSTCONDITION,
    )

    with pytest.raises(
        ValueError,
        match="Contract rule must have type 'invariant'",
    ):
        FinancialContract(
            name="Invalid Contract",
            invariants=(postcondition,),
        )


def test_contract_rejects_wrong_postcondition_rule_type() -> None:
    precondition = ContractRule(
        name="Payment exists",
        expression="payment.exists == true",
        rule_type=ContractRuleType.PRECONDITION,
    )

    with pytest.raises(
        ValueError,
        match="Contract rule must have type 'postcondition'",
    ):
        FinancialContract(
            name="Invalid Contract",
            postconditions=(precondition,),
        )
