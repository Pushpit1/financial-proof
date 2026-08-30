from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.enums.financial import (
    ClaimType,
    ContractAuthorizationAction,
    ContractIdempotencyMode,
    ContractOperator,
    ContractRuleType,
    ContractState,
    ContractTimeRelation,
    ContractTransitionTrigger,
)
from app.domain.models.financial import FinancialContract
from app.domain.services.contract_validator import ContractValidator
from app.domain.value_objects.financial import (
    ContractAuthorization,
    ContractCondition,
    ContractField,
    ContractIdempotencyPolicy,
    ContractRule,
    ContractStateTransition,
    ContractTemporalRule,
    FinancialConstraint,
)


def test_valid_contract_returns_valid_result() -> None:
    contract = FinancialContract(
        name="Income Verification",
        version=1,
        required_claim_types=(ClaimType.INCOME,),
        inputs=(
            ContractField(
                name="monthly_income",
                data_type="money",
            ),
            ContractField(
                name="request_id",
                data_type="uuid",
            ),
        ),
        financial_constraints=(
            FinancialConstraint(
                field="monthly_income",
                operator=ContractOperator.GREATER_THAN_OR_EQUAL,
                value=Decimal("50000"),
                currency="INR",
            ),
        ),
        authorizations=(
            ContractAuthorization(
                actor="underwriter",
                action=ContractAuthorizationAction.EVALUATE,
                resource="financial_proof",
            ),
        ),
        idempotency_policy=ContractIdempotencyPolicy(
            mode=ContractIdempotencyMode.REQUIRED,
            key_field="request_id",
            ttl_seconds=3600,
        ),
        state_transitions=(
            ContractStateTransition(
                from_state=ContractState.DRAFT,
                to_state=ContractState.PROCESSING,
                trigger=ContractTransitionTrigger.EVALUATE,
            ),
        ),
    )

    result = ContractValidator().validate(contract)

    assert result.valid is True
    assert result.errors == ()


def test_validator_returns_immutable_errors() -> None:
    contract = FinancialContract(
        name="Simple Contract",
    )

    result = ContractValidator().validate(contract)

    assert isinstance(result.errors, tuple)


def test_validator_detects_duplicate_required_claim_types() -> None:
    contract = object.__new__(FinancialContract)

    object.__setattr__(contract, "name", "Duplicate Claims")
    object.__setattr__(contract, "version", 1)
    object.__setattr__(contract, "minimum_confidence", None)
    object.__setattr__(
        contract,
        "minimum_supported_claim_ratio",
        Decimal("1"),
    )
    object.__setattr__(
        contract,
        "required_claim_types",
        (ClaimType.INCOME, ClaimType.INCOME),
    )
    object.__setattr__(contract, "preconditions", ())
    object.__setattr__(contract, "invariants", ())
    object.__setattr__(contract, "postconditions", ())
    object.__setattr__(contract, "inputs", ())
    object.__setattr__(contract, "outputs", ())
    object.__setattr__(contract, "financial_constraints", ())
    object.__setattr__(contract, "authorizations", ())
    object.__setattr__(contract, "temporal_rules", ())
    object.__setattr__(contract, "idempotency_policy", None)
    object.__setattr__(contract, "state_transitions", ())

    result = ContractValidator().validate(contract)

    assert result.valid is False
    assert (
        "Duplicate required claim type: 'income'."
        in result.errors
    )


def test_validator_detects_input_output_overlap() -> None:
    field = ContractField(
        name="amount",
        data_type="money",
    )

    contract = object.__new__(FinancialContract)

    object.__setattr__(contract, "name", "Overlap Contract")
    object.__setattr__(contract, "version", 1)
    object.__setattr__(contract, "minimum_confidence", None)
    object.__setattr__(
        contract,
        "minimum_supported_claim_ratio",
        Decimal("1"),
    )
    object.__setattr__(contract, "required_claim_types", ())
    object.__setattr__(contract, "preconditions", ())
    object.__setattr__(contract, "invariants", ())
    object.__setattr__(contract, "postconditions", ())
    object.__setattr__(contract, "inputs", (field,))
    object.__setattr__(contract, "outputs", (field,))
    object.__setattr__(contract, "financial_constraints", ())
    object.__setattr__(contract, "authorizations", ())
    object.__setattr__(contract, "temporal_rules", ())
    object.__setattr__(contract, "idempotency_policy", None)
    object.__setattr__(contract, "state_transitions", ())

    result = ContractValidator().validate(contract)

    assert result.valid is False
    assert (
        "Contract field cannot be both input and output: 'amount'."
        in result.errors
    )


def test_duplicate_authorizations_are_rejected_by_domain() -> None:
    authorization = ContractAuthorization(
        actor="underwriter",
        action=ContractAuthorizationAction.APPROVE,
        resource="financial_proof",
    )

    contract = FinancialContract(
        name="Authorization Contract",
        authorizations=(authorization, authorization),
    )

    result = ContractValidator().validate(contract)

    assert result.valid is False
    assert result.errors == (
        "Duplicate contract authorization.",
    )


def test_validator_detects_duplicate_temporal_rules() -> None:
    rule = ContractTemporalRule(
        field="transaction.created_at",
        relation=ContractTimeRelation.ON_OR_AFTER,
        start=datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        ),
    )

    contract = object.__new__(FinancialContract)

    object.__setattr__(contract, "name", "Temporal Contract")
    object.__setattr__(contract, "version", 1)
    object.__setattr__(contract, "minimum_confidence", None)
    object.__setattr__(
        contract,
        "minimum_supported_claim_ratio",
        Decimal("1"),
    )
    object.__setattr__(contract, "required_claim_types", ())
    object.__setattr__(contract, "preconditions", ())
    object.__setattr__(contract, "invariants", ())
    object.__setattr__(contract, "postconditions", ())
    object.__setattr__(contract, "inputs", ())
    object.__setattr__(contract, "outputs", ())
    object.__setattr__(contract, "financial_constraints", ())
    object.__setattr__(contract, "authorizations", ())
    object.__setattr__(
        contract,
        "temporal_rules",
        (rule, rule),
    )
    object.__setattr__(contract, "idempotency_policy", None)
    object.__setattr__(contract, "state_transitions", ())

    result = ContractValidator().validate(contract)

    assert result.valid is False
    assert result.errors == (
        "Duplicate contract temporal rule.",
    )


def test_validator_detects_invalid_idempotency_reference() -> None:
    contract = object.__new__(FinancialContract)

    object.__setattr__(contract, "name", "Idempotency Contract")
    object.__setattr__(contract, "version", 1)
    object.__setattr__(contract, "minimum_confidence", None)
    object.__setattr__(
        contract,
        "minimum_supported_claim_ratio",
        Decimal("1"),
    )
    object.__setattr__(contract, "required_claim_types", ())
    object.__setattr__(contract, "preconditions", ())
    object.__setattr__(contract, "invariants", ())
    object.__setattr__(contract, "postconditions", ())
    object.__setattr__(
        contract,
        "inputs",
        (
            ContractField(
                name="request_id",
                data_type="uuid",
            ),
        ),
    )
    object.__setattr__(contract, "outputs", ())
    object.__setattr__(contract, "financial_constraints", ())
    object.__setattr__(contract, "authorizations", ())
    object.__setattr__(contract, "temporal_rules", ())
    object.__setattr__(
        contract,
        "idempotency_policy",
        ContractIdempotencyPolicy(
            mode=ContractIdempotencyMode.REQUIRED,
            key_field="wrong_field",
        ),
    )
    object.__setattr__(contract, "state_transitions", ())

    result = ContractValidator().validate(contract)

    assert result.valid is False
    assert (
        "Idempotency key field must reference a declared "
        "contract input field."
        in result.errors
    )


def test_validator_detects_duplicate_transitions() -> None:
    transition = ContractStateTransition(
        from_state=ContractState.DRAFT,
        to_state=ContractState.PROCESSING,
        trigger=ContractTransitionTrigger.EVALUATE,
    )

    contract = object.__new__(FinancialContract)

    object.__setattr__(contract, "name", "Transition Contract")
    object.__setattr__(contract, "version", 1)
    object.__setattr__(contract, "minimum_confidence", None)
    object.__setattr__(
        contract,
        "minimum_supported_claim_ratio",
        Decimal("1"),
    )
    object.__setattr__(contract, "required_claim_types", ())
    object.__setattr__(contract, "preconditions", ())
    object.__setattr__(contract, "invariants", ())
    object.__setattr__(contract, "postconditions", ())
    object.__setattr__(contract, "inputs", ())
    object.__setattr__(contract, "outputs", ())
    object.__setattr__(contract, "financial_constraints", ())
    object.__setattr__(contract, "authorizations", ())
    object.__setattr__(contract, "temporal_rules", ())
    object.__setattr__(contract, "idempotency_policy", None)
    object.__setattr__(
        contract,
        "state_transitions",
        (transition, transition),
    )

    result = ContractValidator().validate(contract)

    assert result.valid is False
    assert result.errors == (
        "Duplicate contract state transition.",
    )


def test_validator_accepts_structured_rule() -> None:
    rule = ContractRule(
        name="Income positive",
        condition=ContractCondition(
            field="monthly_income",
            operator=ContractOperator.GREATER_THAN,
            value=Decimal("0"),
        ),
        rule_type=ContractRuleType.INVARIANT,
    )

    contract = FinancialContract(
        name="Rule Contract",
        invariants=(rule,),
    )

    result = ContractValidator().validate(contract)

    assert result.valid is True
    assert result.errors == ()


def test_domain_rejects_invalid_idempotency_reference() -> None:
    with pytest.raises(
        ValueError,
        match="Idempotency key field must reference",
    ):
        FinancialContract(
            name="Invalid Idempotency",
            inputs=(
                ContractField(
                    name="request_id",
                    data_type="uuid",
                ),
            ),
            idempotency_policy=ContractIdempotencyPolicy(
                mode=ContractIdempotencyMode.REQUIRED,
                key_field="wrong_field",
            ),
        )


def test_domain_rejects_duplicate_state_transition() -> None:
    transition = ContractStateTransition(
        from_state=ContractState.DRAFT,
        to_state=ContractState.PROCESSING,
        trigger=ContractTransitionTrigger.EVALUATE,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate contract state transition",
    ):
        FinancialContract(
            name="Duplicate Transition",
            state_transitions=(transition, transition),
        )
