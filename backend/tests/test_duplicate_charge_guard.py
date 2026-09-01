from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.services.duplicate_charge_guard import DuplicateChargeGuard


def test_new_charge_key_is_allowed() -> None:
    guard = DuplicateChargeGuard()

    result = guard.evaluate(
        idempotency_key="charge-001",
        processed_keys=set(),
    )

    assert result.decision is GuardianDecision.ALLOW


def test_processed_charge_key_is_blocked() -> None:
    guard = DuplicateChargeGuard()

    result = guard.evaluate(
        idempotency_key="charge-001",
        processed_keys={"charge-001"},
    )

    assert result.decision is GuardianDecision.BLOCK
    assert result.rule == "duplicate_charge_prevention"
    assert "already been processed" in result.reason


def test_missing_charge_key_is_blocked() -> None:
    guard = DuplicateChargeGuard()

    result = guard.evaluate(
        idempotency_key="   ",
        processed_keys=set(),
    )

    assert result.decision is GuardianDecision.BLOCK
    assert "idempotency key is missing" in result.reason


def test_charge_key_is_trimmed_before_lookup() -> None:
    guard = DuplicateChargeGuard()

    result = guard.evaluate(
        idempotency_key="  charge-001  ",
        processed_keys={"charge-001"},
    )

    assert result.decision is GuardianDecision.BLOCK


def test_charge_key_matching_is_exact() -> None:
    guard = DuplicateChargeGuard()

    result = guard.evaluate(
        idempotency_key="charge-001",
        processed_keys={"charge-002"},
    )

    assert result.decision is GuardianDecision.ALLOW
