from decimal import Decimal

from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.refund_request import RefundRequest


class RefundApprovalGuard:
    """Deterministically enforce approval for high-value refunds."""

    RULE = "refund_approval"

    def __init__(self, approval_threshold_minor: int) -> None:
        if approval_threshold_minor <= 0:
            raise ValueError(
                "Refund approval threshold must be positive."
            )

        self._threshold = Decimal(approval_threshold_minor)

    def evaluate(
        self,
        request: RefundRequest,
    ) -> GuardianEvaluation:
        """Return whether a refund is permitted by approval policy."""

        amount = Decimal(request.amount_minor)

        if amount <= self._threshold:
            return GuardianEvaluation(
                decision=GuardianDecision.ALLOW,
                rule=self.RULE,
                reason=(
                    "Refund is at or below the approval threshold."
                ),
            )

        if request.approval_granted:
            return GuardianEvaluation(
                decision=GuardianDecision.ALLOW,
                rule=self.RULE,
                reason=(
                    "Refund exceeds the approval threshold "
                    "but required approval is present."
                ),
            )

        return GuardianEvaluation(
            decision=GuardianDecision.BLOCK,
            rule=self.RULE,
            reason=(
                "Refund exceeds the approval threshold "
                "and required approval is missing."
            ),
        )
