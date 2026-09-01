from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.enums.idempotency import IdempotencyStatus
from app.domain.models.financial_guardian import GuardianEvaluation


class IdempotencyGuard:
    """Enforce deterministic runtime idempotency semantics."""

    RULE = "idempotency_enforcement"

    def evaluate(
        self,
        idempotency_key: str,
        status: IdempotencyStatus,
    ) -> GuardianEvaluation:
        """Return whether an operation may proceed."""

        if not idempotency_key.strip():
            return GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule=self.RULE,
                reason="Idempotency key is missing.",
            )

        if status is IdempotencyStatus.COMPLETED:
            return GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule=self.RULE,
                reason=(
                    "Operation has already completed for "
                    "this idempotency key."
                ),
            )

        if status is IdempotencyStatus.PROCESSING:
            return GuardianEvaluation(
                decision=GuardianDecision.REVIEW,
                rule=self.RULE,
                reason=(
                    "Operation is already processing for "
                    "this idempotency key."
                ),
            )

        return GuardianEvaluation(
            decision=GuardianDecision.ALLOW,
            rule=self.RULE,
            reason="Idempotency key represents a new operation.",
        )
