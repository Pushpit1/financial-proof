from decimal import Decimal

from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.services.guardian_policy import GuardianPolicy


def evaluation(
    decision: GuardianDecision,
    reason: str,
) -> GuardianEvaluation:
    return GuardianEvaluation(
        decision=decision,
        rule="test",
        reason=reason,
    )


def test_all_allow_results_in_allow() -> None:
    result = GuardianPolicy.decide(
        [
            evaluation(GuardianDecision.ALLOW, "First allowed."),
            evaluation(GuardianDecision.ALLOW, "Second allowed."),
        ]
    )

    assert result.decision is GuardianDecision.ALLOW


def test_review_overrides_allow() -> None:
    result = GuardianPolicy.decide(
        [
            evaluation(GuardianDecision.ALLOW, "Safe."),
            evaluation(GuardianDecision.REVIEW, "Needs review."),
        ]
    )

    assert result.decision is GuardianDecision.REVIEW


def test_block_overrides_allow() -> None:
    result = GuardianPolicy.decide(
        [
            evaluation(GuardianDecision.ALLOW, "Safe."),
            evaluation(GuardianDecision.BLOCK, "Dangerous."),
        ]
    )

    assert result.decision is GuardianDecision.BLOCK


def test_block_overrides_review() -> None:
    result = GuardianPolicy.decide(
        [
            evaluation(GuardianDecision.REVIEW, "Needs review."),
            evaluation(GuardianDecision.BLOCK, "Blocked."),
        ]
    )

    assert result.decision is GuardianDecision.BLOCK


def test_precedence_is_independent_of_order() -> None:
    evaluations = [
        evaluation(GuardianDecision.ALLOW, "Allowed."),
        evaluation(GuardianDecision.REVIEW, "Review."),
        evaluation(GuardianDecision.BLOCK, "Blocked."),
    ]

    first = GuardianPolicy.decide(evaluations)
    second = GuardianPolicy.decide(tuple(reversed(evaluations)))

    assert first.decision is GuardianDecision.BLOCK
    assert second.decision is GuardianDecision.BLOCK


def test_reasons_are_preserved() -> None:
    result = GuardianPolicy.decide(
        [
            evaluation(GuardianDecision.REVIEW, "Approval missing."),
            evaluation(GuardianDecision.REVIEW, "Additional verification required."),
        ]
    )

    assert "Approval missing." in result.reason
    assert "Additional verification required." in result.reason


def test_empty_evaluations_require_review() -> None:
    result = GuardianPolicy.decide([])

    assert result.decision is GuardianDecision.REVIEW
    assert "No Guardian evaluations" in result.reason


def test_policy_result_is_immutable() -> None:
    result = GuardianPolicy.decide(
        [evaluation(GuardianDecision.ALLOW, "Allowed.")]
    )

    try:
        result.decision = GuardianDecision.BLOCK
    except Exception as exc:
        assert isinstance(exc, (AttributeError, TypeError))
    else:
        raise AssertionError("Guardian policy result must be immutable.")


def test_decimal_import_does_not_change_policy_semantics() -> None:
    amount = Decimal("100.00")

    result = GuardianPolicy.decide(
        [
            evaluation(
                GuardianDecision.ALLOW,
                f"Financial operation for {amount} is allowed.",
            )
        ]
    )

    assert result.decision is GuardianDecision.ALLOW
