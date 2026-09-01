from collections.abc import Sequence

from app.core.logging import get_logger, log_event
from app.core.metrics import get_metrics_registry
from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation

logger = get_logger(__name__)


class GuardianPolicy:
    """Combine individual Guardian evaluations into one final decision."""

    @staticmethod
    def decide(
        evaluations: Sequence[GuardianEvaluation],
    ) -> GuardianEvaluation:
        if not evaluations:
            result = GuardianEvaluation(
                decision=GuardianDecision.REVIEW,
                rule="guardian_policy",
                reason="No Guardian evaluations were provided.",
            )

            get_metrics_registry().counter(
                "guardian_decisions_total",
            ).increment()

            log_event(
                logger,
                "guardian_decision_evaluated",
                fields={
                    "decision": result.decision.value,
                    "rule": result.rule,
                    "reason": result.reason,
                    "evaluation_count": 0,
                },
            )

            return result

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

        result = GuardianEvaluation(
            decision=decision,
            rule="guardian_policy",
            reason=" ".join(reasons),
        )

        get_metrics_registry().counter(
            "guardian_decisions_total",
        ).increment()

        log_event(
            logger,
            "guardian_decision_evaluated",
            fields={
                "decision": result.decision.value,
                "rule": result.rule,
                "reason": result.reason,
                "evaluation_count": len(evaluations),
            },
        )

        return result
