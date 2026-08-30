from datetime import UTC, datetime

import pytest

from app.domain.enums.financial import (
    ContractAuthorizationAction,
    ContractIdempotencyMode,
    ContractState,
    ContractTimeRelation,
    ContractTransitionTrigger,
)
from app.domain.models.financial import FinancialContract
from app.domain.value_objects.financial import (
    ContractAuthorization,
    ContractField,
    ContractIdempotencyPolicy,
    ContractStateTransition,
    ContractTemporalRule,
)


def test_idempotency_policy_supports_required_mode() -> None:
    policy = ContractIdempotencyPolicy(
        mode=ContractIdempotencyMode.REQUIRED,
        key_field="request.idempotency_key",
        ttl_seconds=3600,
    )

    assert policy.mode == ContractIdempotencyMode.REQUIRED
    assert policy.key_field == "request.idempotency_key"
    assert policy.ttl_seconds == 3600


def test_idempotency_policy_is_immutable() -> None:
    policy = ContractIdempotencyPolicy(
        mode=ContractIdempotencyMode.REQUIRED,
        key_field="request.idempotency_key",
    )

    with pytest.raises(AttributeError):
        policy.key_field = "changed"  # type: ignore[misc]


def test_idempotency_policy_requires_key_when_enabled() -> None:
    with pytest.raises(
        ValueError,
        match="Enabled idempotency requires a key field",
    ):
        ContractIdempotencyPolicy(
            mode=ContractIdempotencyMode.REQUIRED,
        )


def test_idempotency_policy_rejects_non_positive_ttl() -> None:
    with pytest.raises(
        ValueError,
        match="Idempotency TTL must be greater than zero",
    ):
        ContractIdempotencyPolicy(
            mode=ContractIdempotencyMode.OPTIONAL,
            key_field="request.idempotency_key",
            ttl_seconds=0,
        )


def test_disabled_idempotency_rejects_key() -> None:
    with pytest.raises(
        ValueError,
        match="Disabled idempotency cannot define a key field",
    ):
        ContractIdempotencyPolicy(
            mode=ContractIdempotencyMode.DISABLED,
            key_field="request.idempotency_key",
        )


def test_state_transition_is_immutable() -> None:
    transition = ContractStateTransition(
        from_state=ContractState.DRAFT,
        to_state=ContractState.PROCESSING,
        trigger=ContractTransitionTrigger.EVALUATE,
    )

    with pytest.raises(AttributeError):
        transition.to_state = ContractState.READY  # type: ignore[misc]


def test_state_transition_supports_valid_transition() -> None:
    transition = ContractStateTransition(
        from_state=ContractState.DRAFT,
        to_state=ContractState.PROCESSING,
        trigger=ContractTransitionTrigger.EVALUATE,
    )

    assert transition.from_state == ContractState.DRAFT
    assert transition.to_state == ContractState.PROCESSING
    assert transition.trigger == ContractTransitionTrigger.EVALUATE


def test_state_transition_rejects_same_state() -> None:
    with pytest.raises(
        ValueError,
        match="Contract state transition must change state",
    ):
        ContractStateTransition(
            from_state=ContractState.READY,
            to_state=ContractState.READY,
            trigger=ContractTransitionTrigger.EVALUATE,
        )


def test_contract_supports_idempotency_and_transitions() -> None:
    contract = FinancialContract(
        name="Financial Decision Contract",
        inputs=(
            ContractField(
                name="request_id",
                data_type="uuid",
            ),
        ),
        authorizations=(
            ContractAuthorization(
                actor="underwriter",
                action=ContractAuthorizationAction.EVALUATE,
                resource="financial_proof",
            ),
        ),
        temporal_rules=(
            ContractTemporalRule(
                field="request.created_at",
                relation=ContractTimeRelation.ON_OR_AFTER,
                start=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=UTC,
                ),
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
            ContractStateTransition(
                from_state=ContractState.PROCESSING,
                to_state=ContractState.READY,
                trigger=ContractTransitionTrigger.VERIFY,
            ),
        ),
    )

    assert contract.idempotency_policy is not None
    assert contract.idempotency_policy.mode == (
        ContractIdempotencyMode.REQUIRED
    )
    assert len(contract.state_transitions) == 2


def test_contract_rejects_duplicate_state_transition() -> None:
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
            name="Duplicate Transition Contract",
            state_transitions=(transition, transition),
        )
