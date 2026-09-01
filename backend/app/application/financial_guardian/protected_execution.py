from dataclasses import dataclass
from decimal import Decimal

from app.application.financial_guardian.runtime import FinancialGuardianRuntime
from app.application.ports.payment_gateway import (
    PaymentCapture,
    PaymentGatewayPort,
    PaymentRefund,
)
from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.contract_authorization import (
    ContractAuthorizationRequest,
    FinancialOperation,
)
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.refund_authorization import RefundAuthorization
from app.domain.models.refund_request import RefundRequest
from app.domain.services.contract_aware_authorization_guard import (
    ContractAwareAuthorizationGuard,
)
from app.domain.services.refund_approval_guard import RefundApprovalGuard
from app.domain.services.unauthorized_refund_guard import UnauthorizedRefundGuard


class FinancialActionDenied(PermissionError):
    """Raised when a sensitive financial action is denied."""


@dataclass(frozen=True)
class FinancialActionAuthorization:
    """Immutable authorization context for a sensitive financial action."""

    actor_id: str
    operation: FinancialOperation
    actor_authorized: bool
    operation_authorized: bool

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("Actor ID cannot be empty.")


class ProtectedFinancialExecutionService:
    """Execute sensitive financial actions only after Guardian authorization."""

    def __init__(
        self,
        gateway: PaymentGatewayPort,
        *,
        guardian_runtime: FinancialGuardianRuntime | None = None,
        refund_approval_threshold_minor: int = 10000,
    ) -> None:
        self._gateway = gateway
        self._guardian_runtime = guardian_runtime or FinancialGuardianRuntime()
        self._authorization_guard = ContractAwareAuthorizationGuard()
        self._refund_approval_guard = RefundApprovalGuard(
            approval_threshold_minor=refund_approval_threshold_minor,
        )
        self._unauthorized_refund_guard = UnauthorizedRefundGuard()

    def refund(
        self,
        *,
        provider_payment_id: str,
        request: RefundRequest,
        authorization: FinancialActionAuthorization,
    ) -> PaymentRefund:
        """Authorize, Guardian-check, then execute a refund."""

        self._require_operation(
            authorization,
            FinancialOperation.REFUND,
        )

        refund_authorization = RefundAuthorization(
            actor_id=authorization.actor_id,
            authorized=(
                authorization.actor_authorized
                and authorization.operation_authorized
            ),
        )

        contract_decision, contract_reason = (
            self._authorization_guard.evaluate(
                ContractAuthorizationRequest(
                    actor_id=authorization.actor_id,
                    operation=FinancialOperation.REFUND,
                    actor_authorized=authorization.actor_authorized,
                    operation_authorized=authorization.operation_authorized,
                )
            )
        )

        evaluations = [
            self._evaluation_from_authorization(
                contract_decision,
                contract_reason,
            ),
            self._unauthorized_refund_guard.evaluate(
                refund_authorization,
            ),
            self._refund_approval_guard.evaluate(request),
        ]

        decision = self._guardian_runtime.decide(
            evaluations,
            operation=FinancialOperation.REFUND.value,
            actor_id=authorization.actor_id,
        )

        self._require_allowed(decision)

        return self._gateway.refund_payment(
            provider_payment_id=provider_payment_id,
            amount=Decimal(request.amount_minor) / Decimal("100"),
        )

    def capture(
        self,
        *,
        provider_payment_id: str,
        amount: Decimal,
        currency: str,
        authorization: FinancialActionAuthorization,
    ) -> PaymentCapture:
        """Authorize, Guardian-check, then execute a payment capture."""

        self._require_operation(
            authorization,
            FinancialOperation.CHARGE,
        )

        contract_decision, contract_reason = (
            self._authorization_guard.evaluate(
                ContractAuthorizationRequest(
                    actor_id=authorization.actor_id,
                    operation=FinancialOperation.CHARGE,
                    actor_authorized=authorization.actor_authorized,
                    operation_authorized=authorization.operation_authorized,
                )
            )
        )

        decision = self._guardian_runtime.decide(
            [
                self._evaluation_from_authorization(
                    contract_decision,
                    contract_reason,
                )
            ],
            operation=FinancialOperation.CHARGE.value,
            actor_id=authorization.actor_id,
        )

        self._require_allowed(decision)

        return self._gateway.capture_payment(
            provider_payment_id=provider_payment_id,
            amount=amount,
            currency=currency,
        )

    def _require_operation(
        self,
        authorization: FinancialActionAuthorization,
        operation: FinancialOperation,
    ) -> None:
        if authorization.operation is not operation:
            raise FinancialActionDenied(
                f"Authorization is for '{authorization.operation.value}', "
                f"not '{operation.value}'."
            )

    @staticmethod
    def _evaluation_from_authorization(
        decision: GuardianDecision,
        reason: str,
    ) -> GuardianEvaluation:
        return GuardianEvaluation(
            decision=decision,
            rule=ContractAwareAuthorizationGuard.RULE,
            reason=reason,
        )

    @staticmethod
    def _require_allowed(
        evaluation: GuardianEvaluation,
    ) -> None:
        if evaluation.decision is not GuardianDecision.ALLOW:
            raise FinancialActionDenied(
                "Financial action was denied by the Financial Guardian."
            )

