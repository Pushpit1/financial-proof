from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.services.duplicate_fulfillment_guard import (
    DuplicateFulfillmentGuard,
)


def test_new_fulfillment_key_is_allowed() -> None:
    guard = DuplicateFulfillmentGuard()

    result = guard.evaluate(
        fulfillment_key="fulfillment-001",
        processed_keys=set(),
    )

    assert result.decision is GuardianDecision.ALLOW


def test_processed_fulfillment_key_is_blocked() -> None:
    guard = DuplicateFulfillmentGuard()

    result = guard.evaluate(
        fulfillment_key="fulfillment-001",
        processed_keys={"fulfillment-001"},
    )

    assert result.decision is GuardianDecision.BLOCK
    assert result.rule == "duplicate_fulfillment_prevention"
    assert "already been processed" in result.reason


def test_missing_fulfillment_key_is_blocked() -> None:
    guard = DuplicateFulfillmentGuard()

    result = guard.evaluate(
        fulfillment_key="   ",
        processed_keys=set(),
    )

    assert result.decision is GuardianDecision.BLOCK
    assert "idempotency key is missing" in result.reason


def test_fulfillment_key_is_trimmed_before_lookup() -> None:
    guard = DuplicateFulfillmentGuard()

    result = guard.evaluate(
        fulfillment_key="  fulfillment-001  ",
        processed_keys={"fulfillment-001"},
    )

    assert result.decision is GuardianDecision.BLOCK


def test_fulfillment_key_matching_is_exact() -> None:
    guard = DuplicateFulfillmentGuard()

    result = guard.evaluate(
        fulfillment_key="fulfillment-001",
        processed_keys={"fulfillment-002"},
    )

    assert result.decision is GuardianDecision.ALLOW
