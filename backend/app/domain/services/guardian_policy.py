from collections.abc import Sequence

from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation


class GuardianPolicy:
    """Combine multiple Guardian evaluations deterministically."""

    @staticmethod
    def decide(
        evaluations: Sequence[GuardianEvaluation],
    ) -> GuardianEvaluation:
        """Return one final decision using strict safety precedence."""

        if not evaluations:
            return GuardianEvaluation(
                decision=GuardianDecision.REVIEW,
                rule="guardian_policy",
                reason="No Guardian evaluations were provided.",
            )

        if any(
            evaluation.decision is GuardianDecision.BLOCK
            for evaluation in evaluations
        ):
            decision = GuardianDecision.BLOCK
        elif any(
            evaluation.decision is GuardianDecision.REVIEW
            for evaluation in evaluations
        ):
            decision = GuardianDecision.REVIEW
        else:
            decision = GuardianDecision.ALLOW

        reasons = tuple(
            evaluation.reason
            for evaluation in evaluations
            if evaluation.reason
        )

        return GuardianEvaluation(
            decision=decision,
            rule="guardian_policy",
            reason=" ".join(reasons),
        )
