from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation


def test_guardian_evaluation_is_immutable() -> None:
    evaluation = GuardianEvaluation(
        decision=GuardianDecision.ALLOW,
        rule="refund_approval",
        reason="Refund is within the permitted threshold.",
    )

    try:
        evaluation.decision = GuardianDecision.BLOCK
    except Exception as exc:
        assert isinstance(exc, AttributeError)

    else:
        raise AssertionError("Guardian evaluation must be immutable.")


def test_guardian_decisions_are_explicit() -> None:
    assert GuardianDecision.ALLOW.value == "allow"
    assert GuardianDecision.BLOCK.value == "block"
    assert GuardianDecision.REVIEW.value == "review"
