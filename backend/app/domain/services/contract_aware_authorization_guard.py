from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.contract_authorization import (
    ContractAuthorizationRequest,
)


class ContractAwareAuthorizationGuard:
    """Enforce authorization at both actor and contract-operation level."""

    RULE = "contract_aware_authorization"

    def evaluate(
        self,
        request: ContractAuthorizationRequest,
    ):
        """Return the deterministic authorization decision."""

        if not request.actor_authorized:
            return GuardianDecision.BLOCK, (
                "Actor is not authorized to perform "
                "financial operations."
            )

        if not request.operation_authorized:
            return GuardianDecision.BLOCK, (
                f"Operation '{request.operation.value}' "
                "is not authorized by the financial contract."
            )

        return GuardianDecision.ALLOW, (
            f"Actor and operation '{request.operation.value}' "
            "are authorized by the financial contract."
        )
