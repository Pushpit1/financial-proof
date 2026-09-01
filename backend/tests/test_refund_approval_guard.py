from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.refund_request import RefundRequest
from app.domain.services.refund_approval_guard import RefundApprovalGuard


def test_refund_at_threshold_is_allowed() -> None:
    guard = RefundApprovalGuard(approval_threshold_minor=10000)

    result = guard.evaluate(
        RefundRequest(
            amount_minor=10000,
            currency="INR",
        )
    )

    assert result.decision is GuardianDecision.ALLOW


def test_refund_below_threshold_is_allowed() -> None:
    guard = RefundApprovalGuard(approval_threshold_minor=10000)

    result = guard.evaluate(
        RefundRequest(
            amount_minor=9999,
            currency="INR",
        )
    )

    assert result.decision is GuardianDecision.ALLOW


def test_refund_above_threshold_without_approval_is_blocked() -> None:
    guard = RefundApprovalGuard(approval_threshold_minor=10000)

    result = guard.evaluate(
        RefundRequest(
            amount_minor=10001,
            currency="INR",
        )
    )

    assert result.decision is GuardianDecision.BLOCK
    assert result.rule == "refund_approval"
    assert "approval is missing" in result.reason


def test_refund_above_threshold_with_approval_is_allowed() -> None:
    guard = RefundApprovalGuard(approval_threshold_minor=10000)

    result = guard.evaluate(
        RefundRequest(
            amount_minor=10001,
            currency="INR",
            approval_granted=True,
        )
    )

    assert result.decision is GuardianDecision.ALLOW


def test_threshold_must_be_positive() -> None:
    try:
        RefundApprovalGuard(approval_threshold_minor=0)
    except ValueError as exc:
        assert str(exc) == (
            "Refund approval threshold must be positive."
        )
    else:
        raise AssertionError("Expected ValueError.")
