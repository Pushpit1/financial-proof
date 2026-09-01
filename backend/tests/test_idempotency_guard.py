from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.enums.idempotency import IdempotencyStatus
from app.domain.services.idempotency_guard import IdempotencyGuard


def test_new_idempotency_key_is_allowed() -> None:
    result = IdempotencyGuard().evaluate(
        "operation-001",
        IdempotencyStatus.NEW,
    )

    assert result.decision is GuardianDecision.ALLOW


def test_completed_idempotency_key_is_blocked() -> None:
    result = IdempotencyGuard().evaluate(
        "operation-001",
        IdempotencyStatus.COMPLETED,
    )

    assert result.decision is GuardianDecision.BLOCK
    assert "already completed" in result.reason


def test_processing_idempotency_key_requires_review() -> None:
    result = IdempotencyGuard().evaluate(
        "operation-001",
        IdempotencyStatus.PROCESSING,
    )

    assert result.decision is GuardianDecision.REVIEW
    assert "already processing" in result.reason


def test_missing_idempotency_key_is_blocked() -> None:
    result = IdempotencyGuard().evaluate(
        "   ",
        IdempotencyStatus.NEW,
    )

    assert result.decision is GuardianDecision.BLOCK
    assert result.rule == "idempotency_enforcement"


def test_idempotency_status_values_are_explicit() -> None:
    assert IdempotencyStatus.NEW.value == "new"
    assert IdempotencyStatus.PROCESSING.value == "processing"
    assert IdempotencyStatus.COMPLETED.value == "completed"
