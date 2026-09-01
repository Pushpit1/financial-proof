from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation


class DuplicateChargeGuard:
    """Prevent execution of an already-processed charge."""

    RULE = "duplicate_charge_prevention"

    def evaluate(
        self,
        idempotency_key: str,
        processed_keys: set[str],
    ) -> GuardianEvaluation:
        """Return whether a charge may be executed."""

        normalized_key = idempotency_key.strip()

        if not normalized_key:
            return GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule=self.RULE,
                reason="Charge idempotency key is missing.",
            )

        if normalized_key in processed_keys:
            return GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule=self.RULE,
                reason=(
                    "Charge has already been processed for "
                    "this idempotency key."
                ),
            )

        return GuardianEvaluation(
            decision=GuardianDecision.ALLOW,
            rule=self.RULE,
            reason="Charge idempotency key has not been processed.",
        )
