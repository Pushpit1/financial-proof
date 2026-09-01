from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.refund_authorization import RefundAuthorization


class UnauthorizedRefundGuard:
    """Prevent refunds initiated by unauthorized actors."""

    RULE = "unauthorized_refund_prevention"

    def evaluate(
        self,
        authorization: RefundAuthorization,
    ) -> GuardianEvaluation:
        """Return whether the refund actor is authorized."""

        if not authorization.authorized:
            return GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule=self.RULE,
                reason=(
                    "Refund actor is not authorized to perform "
                    "this operation."
                ),
            )

        return GuardianEvaluation(
            decision=GuardianDecision.ALLOW,
            rule=self.RULE,
            reason="Refund actor is authorized to perform this operation.",
        )
