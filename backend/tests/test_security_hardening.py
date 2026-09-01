"""End-to-end security hardening regression tests."""

from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import app.api.dependencies.authentication as authentication
from app.api.dependencies.authorization import require_permission
from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)
from app.application.ai_investigation.registry import InvestigationToolRegistry
from app.application.financial_guardian import (
    FinancialActionAuthorization,
    FinancialActionDenied,
    ProtectedFinancialExecutionService,
)
from app.application.ports.webhook_replay import InMemoryWebhookReplayStore
from app.application.services.razorpay_webhook import RazorpayWebhookService
from app.core.authorization import Permission
from app.core.config import Settings
from app.core.redaction import REDACTED_VALUE, redact_sensitive_data
from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.contract_authorization import FinancialOperation
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.refund_request import RefundRequest


def configure_test_authentication() -> None:
    authentication.settings = Settings(
        database_url=(
            "postgresql+psycopg://financial_proof:"
            "test-password@localhost:5433/financial_proof"
        ),
        api_auth_token="financial-proof-development-token",
    )
    authentication.get_authenticator.cache_clear()


def test_missing_api_credentials_are_fail_closed() -> None:
    configure_test_authentication()

    app = FastAPI()

    @app.get(
        "/protected",
        dependencies=[
            Depends(require_permission(Permission.READ_FINANCIAL_DATA)),
        ],
    )
    def protected() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).get("/protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_insufficient_api_permissions_are_denied() -> None:
    configure_test_authentication()

    app = FastAPI()

    @app.get(
        "/admin-only",
        dependencies=[
            Depends(require_permission(Permission.MANAGE_GUARDIAN)),
        ],
    )
    def admin_only() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).get(
        "/admin-only",
        headers={
            "Authorization": "Bearer financial-proof-development-token",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied."}


def test_ai_tool_cannot_execute_undeclared_arguments() -> None:
    executed = False

    def handler(
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        nonlocal executed
        executed = True

        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"executed": True},
        )

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_CONTRACT: handler,
        },
        permissions={
            InvestigationTool.INSPECT_CONTRACT,
        },
    )

    result = registry.execute(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=uuid4(),
            arguments={"execute": True},
        )
    )

    assert result.status is ToolExecutionStatus.DENIED
    assert executed is False


def test_guardian_denial_prevents_refund_gateway_call() -> None:
    gateway = Mock()
    service = ProtectedFinancialExecutionService(
        gateway,
        refund_approval_threshold_minor=10000,
    )

    authorization = FinancialActionAuthorization(
        actor_id="operator-001",
        operation=FinancialOperation.REFUND,
        actor_authorized=False,
        operation_authorized=True,
    )

    with pytest.raises(FinancialActionDenied):
        service.refund(
            provider_payment_id="pay_001",
            request=RefundRequest(
                amount_minor=5000,
                currency="INR",
            ),
            authorization=authorization,
        )

    gateway.refund_payment.assert_not_called()


def test_guardian_review_does_not_execute_financial_action() -> None:
    gateway = Mock()

    runtime = Mock()
    runtime.decide.return_value = GuardianEvaluation(
        decision=GuardianDecision.REVIEW,
        rule="security_regression",
        reason="Manual review required.",
    )

    service = ProtectedFinancialExecutionService(
        gateway,
        guardian_runtime=runtime,
    )

    authorization = FinancialActionAuthorization(
        actor_id="operator-001",
        operation=FinancialOperation.CHARGE,
        actor_authorized=True,
        operation_authorized=True,
    )

    with pytest.raises(FinancialActionDenied):
        service.capture(
            provider_payment_id="pay_001",
            amount=Decimal("100.00"),
            currency="INR",
            authorization=authorization,
        )

    gateway.capture_payment.assert_not_called()


def test_operation_confusion_cannot_cross_financial_boundary() -> None:
    gateway = Mock()

    service = ProtectedFinancialExecutionService(gateway)

    authorization = FinancialActionAuthorization(
        actor_id="operator-001",
        operation=FinancialOperation.REFUND,
        actor_authorized=True,
        operation_authorized=True,
    )

    with pytest.raises(FinancialActionDenied):
        service.capture(
            provider_payment_id="pay_001",
            amount=Decimal("100.00"),
            currency="INR",
            authorization=authorization,
        )

    gateway.capture_payment.assert_not_called()


def test_webhook_replay_is_rejected_after_successful_claim() -> None:
    gateway = Mock()
    gateway.verify_webhook_signature.return_value = True

    service = RazorpayWebhookService(
        gateway,
        InMemoryWebhookReplayStore(),
    )

    request = {
        "payload": b'{"event":"payment.captured"}',
        "signature": "valid-signature",
        "event_id": "evt-security-001",
    }

    from app.application.dto.razorpay_webhook import (
        RazorpayWebhookVerificationRequest,
    )

    first = service.verify(
        RazorpayWebhookVerificationRequest(**request)
    )
    second = service.verify(
        RazorpayWebhookVerificationRequest(**request)
    )

    assert first.valid is True
    assert second.valid is False
    assert second.replayed is True
    assert gateway.verify_webhook_signature.call_count == 2


def test_sensitive_values_never_survive_redaction() -> None:
    secret_values = (
        "Bearer ultra-secret-token",
        "razorpay-secret",
        "webhook-signature-secret",
        "api-key-secret",
    )

    result = redact_sensitive_data(
        {
            "authorization": secret_values[0],
            "key_secret": secret_values[1],
            "signature": secret_values[2],
            "api_key": secret_values[3],
            "operation": "refund",
            "amount_minor": 5000,
        }
    )

    encoded = repr(result)

    for secret in secret_values:
        assert secret not in encoded

    assert result["authorization"] == REDACTED_VALUE
    assert result["key_secret"] == REDACTED_VALUE
    assert result["signature"] == REDACTED_VALUE
    assert result["api_key"] == REDACTED_VALUE
    assert result["operation"] == "refund"
    assert result["amount_minor"] == 5000
