from decimal import Decimal

import pytest

from app.domain.enums.financial import (
    ClaimType,
    ContractOperator,
    ContractRuleType,
)
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import (
    ConfidenceScore,
    ContractCondition,
    ContractField,
    ContractRule,
)


def test_financial_contract_defaults() -> None:
    contract = FinancialContract(
        name="Standard Financial Review",
    )

    assert contract.version == 1
    assert contract.minimum_confidence == ConfidenceScore(
        Decimal("0")
    )
    assert contract.minimum_supported_claim_ratio == Decimal("1")
    assert contract.required_claim_types == ()
    assert contract.preconditions == ()
    assert contract.invariants == ()
    assert contract.postconditions == ()
    assert contract.inputs == ()
    assert contract.outputs == ()


def test_financial_contract_supports_required_claim_types() -> None:
    contract = FinancialContract(
        name="Income Verification",
        version=2,
        minimum_confidence=ConfidenceScore(Decimal("0.80")),
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
    [Decimal("-0.01"), Decimal("1.01")],
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
    contract = FinancialContract(name="Immutable Contract")

    with pytest.raises(AttributeError):
        contract.name = "Changed"  # type: ignore[misc]


def test_contract_condition_is_immutable() -> None:
    condition = ContractCondition(
        field="payment.amount",
        operator=ContractOperator.GREATER_THAN,
        value=Decimal("0"),
    )

    with pytest.raises(AttributeError):
        condition.field = "changed"  # type: ignore[misc]


def test_contract_condition_supports_comparison() -> None:
    condition = ContractCondition(
        field="payment.amount",
        operator=ContractOperator.GREATER_THAN,
        value=Decimal("0"),
    )

    assert condition.field == "payment.amount"
    assert condition.operator == ContractOperator.GREATER_THAN
    assert condition.value == Decimal("0")


def test_contract_condition_supports_existence() -> None:
    condition = ContractCondition(
        field="payment.id",
        operator=ContractOperator.EXISTS,
    )

    assert condition.value is None


def test_contract_condition_supports_membership() -> None:
    condition = ContractCondition(
        field="payment.status",
        operator=ContractOperator.IN,
        value=("captured", "authorized"),
    )

    assert condition.value == ("captured", "authorized")


def test_contract_condition_rejects_empty_field() -> None:
    with pytest.raises(
        ValueError,
        match="Contract condition field cannot be empty",
    ):
        ContractCondition(
            field="",
            operator=ContractOperator.EXISTS,
        )


def test_contract_condition_rejects_surrounding_field_whitespace() -> None:
    with pytest.raises(
        ValueError,
        match="Contract condition field cannot contain surrounding whitespace",
    ):
        ContractCondition(
            field=" payment.amount ",
            operator=ContractOperator.GREATER_THAN,
            value=Decimal("0"),
        )


def test_contract_condition_rejects_value_for_exists() -> None:
    with pytest.raises(
        ValueError,
        match="Existence conditions cannot define a value",
    ):
        ContractCondition(
            field="payment.id",
            operator=ContractOperator.EXISTS,
            value=True,
        )


def test_contract_condition_rejects_missing_comparison_value() -> None:
    with pytest.raises(
        ValueError,
        match="Contract condition value cannot be empty",
    ):
        ContractCondition(
            field="payment.amount",
            operator=ContractOperator.GREATER_THAN,
        )


def test_contract_condition_rejects_non_collection_membership_value() -> None:
    with pytest.raises(
        ValueError,
        match="Membership condition value must be a collection",
    ):
        ContractCondition(
            field="payment.status",
            operator=ContractOperator.IN,
            value="captured",
        )


def test_contract_condition_rejects_empty_membership_value() -> None:
    with pytest.raises(
        ValueError,
        match="Membership condition value cannot be empty",
    ):
        ContractCondition(
            field="payment.status",
            operator=ContractOperator.IN,
            value=(),
        )


def test_contract_rule_contains_structured_condition() -> None:
    condition = ContractCondition(
        field="payment.amount",
        operator=ContractOperator.GREATER_THAN,
        value=Decimal("0"),
    )

    rule = ContractRule(
        name="Payment amount positive",
        condition=condition,
        rule_type=ContractRuleType.INVARIANT,
    )

    assert rule.condition == condition
    assert rule.rule_type == ContractRuleType.INVARIANT


def test_contract_supports_structured_rules() -> None:
    precondition = ContractRule(
        name="Payment exists",
        condition=ContractCondition(
            field="payment.id",
            operator=ContractOperator.EXISTS,
        ),
        rule_type=ContractRuleType.PRECONDITION,
    )

    invariant = ContractRule(
        name="Payment positive",
        condition=ContractCondition(
            field="payment.amount",
            operator=ContractOperator.GREATER_THAN,
            value=Decimal("0"),
        ),
        rule_type=ContractRuleType.INVARIANT,
    )

    postcondition = ContractRule(
        name="Refund linked",
        condition=ContractCondition(
            field="refund.original_payment_id",
            operator=ContractOperator.EXISTS,
        ),
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


def test_contract_field_is_immutable() -> None:
    contract_field = ContractField(
        name="payment_id",
        data_type="uuid",
    )

    with pytest.raises(AttributeError):
        contract_field.name = "changed"  # type: ignore[misc]


def test_contract_field_has_unique_ids() -> None:
    first = ContractField(
        name="payment_id",
        data_type="uuid",
    )
    second = ContractField(
        name="amount",
        data_type="money",
    )

    assert first.id != second.id


def test_contract_field_rejects_empty_name() -> None:
    with pytest.raises(
        ValueError,
        match="Contract field name cannot be empty",
    ):
        ContractField(
            name="",
            data_type="uuid",
        )


def test_contract_field_rejects_empty_data_type() -> None:
    with pytest.raises(
        ValueError,
        match="Contract field data type cannot be empty",
    ):
        ContractField(
            name="payment_id",
            data_type=" ",
        )


def test_contract_field_rejects_surrounding_name_whitespace() -> None:
    with pytest.raises(
        ValueError,
        match="Contract field name cannot contain surrounding whitespace",
    ):
        ContractField(
            name=" payment_id ",
            data_type="uuid",
        )


def test_contract_field_rejects_surrounding_data_type_whitespace() -> None:
    with pytest.raises(
        ValueError,
        match="Contract field data type cannot contain surrounding whitespace",
    ):
        ContractField(
            name="payment_id",
            data_type=" uuid ",
        )


def test_contract_supports_inputs_and_outputs() -> None:
    payment_id = ContractField(
        name="payment_id",
        data_type="uuid",
    )
    amount = ContractField(
        name="amount",
        data_type="money",
    )
    refund_id = ContractField(
        name="refund_id",
        data_type="uuid",
        required=False,
    )

    contract = FinancialContract(
        name="Refund Contract",
        inputs=(payment_id, amount),
        outputs=(refund_id,),
    )

    assert contract.inputs == (payment_id, amount)
    assert contract.outputs == (refund_id,)


def test_contract_rejects_duplicate_input_fields() -> None:
    first = ContractField(
        name="payment_id",
        data_type="uuid",
    )
    second = ContractField(
        name="payment_id",
        data_type="string",
    )

    with pytest.raises(
        ValueError,
        match="Duplicate contract input field",
    ):
        FinancialContract(
            name="Invalid Contract",
            inputs=(first, second),
        )


def test_contract_rejects_duplicate_output_fields() -> None:
    first = ContractField(
        name="refund_id",
        data_type="uuid",
    )
    second = ContractField(
        name="refund_id",
        data_type="string",
    )

    with pytest.raises(
        ValueError,
        match="Duplicate contract output field",
    ):
        FinancialContract(
            name="Invalid Contract",
            outputs=(first, second),
        )
