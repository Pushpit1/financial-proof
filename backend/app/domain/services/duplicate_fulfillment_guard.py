from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation


class DuplicateFulfillmentGuard:
    """Prevent execution of an already-processed fulfillment."""

    RULE = "duplicate_fulfillment_prevention"

    def evaluate(
        self,
        fulfillment_key: str,
        processed_keys: set[str],
    ) -> GuardianEvaluation:
        """Return whether a fulfillment may be executed."""

        normalized_key = fulfillment_key.strip()

        if not normalized_key:
            return GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule=self.RULE,
                reason="Fulfillment idempotency key is missing.",
            )

        if normalized_key in processed_keys:
            return GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule=self.RULE,
                reason=(
                    "Fulfillment has already been processed for "
                    "this idempotency key."
                ),
            )

        return GuardianEvaluation(
            decision=GuardianDecision.ALLOW,
            rule=self.RULE,
            reason=(
                "Fulfillment idempotency key has not been processed."
            ),
        )
