from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.application.financial_guardian import (
    FinancialActionAuthorization,
    FinancialActionDenied,
    ProtectedFinancialExecutionService,
)
from app.application.ports.payment_gateway import PaymentRefund
from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.contract_authorization import FinancialOperation
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.refund_request import RefundRequest


def authorization(
    *,
    actor_authorized: bool = True,
    operation_authorized: bool = True,
) -> FinancialActionAuthorization:
    return FinancialActionAuthorization(
        actor_id="operator-001",
        operation=FinancialOperation.REFUND,
        actor_authorized=actor_authorized,
        operation_authorized=operation_authorized,
    )


def test_refund_requires_authorization_before_gateway_execution() -> None:
    gateway = Mock()
    service = ProtectedFinancialExecutionService(
        gateway,
        refund_approval_threshold_minor=10000,
    )

    with pytest.raises(FinancialActionDenied):
        service.refund(
            provider_payment_id="pay_001",
            request=RefundRequest(
                amount_minor=5000,
                currency="INR",
            ),
            authorization=authorization(actor_authorized=False),
        )

    gateway.refund_payment.assert_not_called()


def test_refund_requires_contract_operation_authorization() -> None:
    gateway = Mock()
    service = ProtectedFinancialExecutionService(gateway)

    with pytest.raises(FinancialActionDenied):
        service.refund(
            provider_payment_id="pay_001",
            request=RefundRequest(
                amount_minor=5000,
                currency="INR",
            ),
            authorization=authorization(operation_authorized=False),
        )

    gateway.refund_payment.assert_not_called()


def test_high_value_refund_without_approval_is_blocked() -> None:
    gateway = Mock()
    service = ProtectedFinancialExecutionService(
        gateway,
        refund_approval_threshold_minor=10000,
    )

    with pytest.raises(FinancialActionDenied):
        service.refund(
            provider_payment_id="pay_001",
            request=RefundRequest(
                amount_minor=10001,
                currency="INR",
            ),
            authorization=authorization(),
        )

    gateway.refund_payment.assert_not_called()


def test_high_value_refund_with_authorization_and_approval_executes() -> None:
    gateway = Mock()
    gateway.refund_payment.return_value = PaymentRefund(
        provider_refund_id="rfnd_001",
        provider_payment_id="pay_001",
        amount=Decimal("100.01"),
        currency="INR",
    )

    service = ProtectedFinancialExecutionService(
        gateway,
        refund_approval_threshold_minor=10000,
    )

    result = service.refund(
        provider_payment_id="pay_001",
        request=RefundRequest(
            amount_minor=10001,
            currency="INR",
            approval_granted=True,
        ),
        authorization=authorization(),
    )

    assert result.provider_refund_id == "rfnd_001"
    gateway.refund_payment.assert_called_once_with(
        provider_payment_id="pay_001",
        amount=Decimal("100.01"),
    )


def test_guardian_review_also_prevents_gateway_execution() -> None:
    gateway = Mock()
    runtime = Mock()
    runtime.decide.return_value = GuardianEvaluation(
        decision=GuardianDecision.REVIEW,
        rule="guardian_policy",
        reason="Manual review required.",
    )

    service = ProtectedFinancialExecutionService(
        gateway,
        guardian_runtime=runtime,
    )

    with pytest.raises(FinancialActionDenied):
        service.refund(
            provider_payment_id="pay_001",
            request=RefundRequest(
                amount_minor=5000,
                currency="INR",
            ),
            authorization=authorization(),
        )

    gateway.refund_payment.assert_not_called()


def test_guardian_block_prevents_gateway_execution() -> None:
    gateway = Mock()
    runtime = Mock()
    runtime.decide.return_value = GuardianEvaluation(
        decision=GuardianDecision.BLOCK,
        rule="guardian_policy",
        reason="Financial operation blocked.",
    )

    service = ProtectedFinancialExecutionService(
        gateway,
        guardian_runtime=runtime,
    )

    with pytest.raises(FinancialActionDenied):
        service.refund(
            provider_payment_id="pay_001",
            request=RefundRequest(
                amount_minor=5000,
                currency="INR",
            ),
            authorization=authorization(),
        )

    gateway.refund_payment.assert_not_called()


def test_operation_confusion_cannot_reuse_refund_authorization_for_capture() -> None:
    gateway = Mock()
    service = ProtectedFinancialExecutionService(gateway)

    with pytest.raises(FinancialActionDenied):
        service.capture(
            provider_payment_id="pay_001",
            amount=Decimal("100.00"),
            currency="INR",
            authorization=authorization(),
        )

    gateway.capture_payment.assert_not_called()


def test_empty_actor_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        FinancialActionAuthorization(
            actor_id="   ",
            operation=FinancialOperation.REFUND,
            actor_authorized=True,
            operation_authorized=True,
        )


