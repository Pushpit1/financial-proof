from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.api.dependencies import get_razorpay_webhook_service
from app.application.dto.razorpay_webhook import (
    RazorpayWebhookVerificationResult,
)
from app.application.ports.webhook_replay import InMemoryWebhookReplayStore
from app.application.services.razorpay_webhook import RazorpayWebhookService
from app.infrastructure.razorpay_adapter import RazorpayProviderError
from app.main import create_app


def build_client(service) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_razorpay_webhook_service] = lambda: service
    return TestClient(app)


def test_razorpay_webhook_accepts_valid_signature() -> None:
    service = Mock()
    service.verify.return_value = RazorpayWebhookVerificationResult(
        valid=True,
    )

    client = build_client(service)

    payload = b'{"event":"payment.captured","id":"evt_123"}'

    response = client.post(
        "/webhooks/razorpay",
        content=payload,
        headers={"X-Razorpay-Signature": "signature_123"},
    )

    assert response.status_code == 200
    assert response.json() == {"valid": True}

    service.verify.assert_called_once()

    request = service.verify.call_args.args[0]

    assert request.payload == payload
    assert request.signature == "signature_123"
    assert request.event_id == "evt_123"


def test_razorpay_webhook_rejects_missing_signature() -> None:
    service = Mock()
    client = build_client(service)

    response = client.post(
        "/webhooks/razorpay",
        content=b'{"event":"payment.captured","id":"evt_123"}',
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "X-Razorpay-Signature header is required."
    )

    service.verify.assert_not_called()


def test_razorpay_webhook_rejects_invalid_signature() -> None:
    service = Mock()
    service.verify.return_value = RazorpayWebhookVerificationResult(
        valid=False,
    )

    client = build_client(service)

    response = client.post(
        "/webhooks/razorpay",
        content=b'{"event":"payment.captured","id":"evt_123"}',
        headers={"X-Razorpay-Signature": "invalid"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid Razorpay webhook signature."
    )


def test_razorpay_webhook_rejects_empty_payload() -> None:
    service = Mock()
    client = build_client(service)

    response = client.post(
        "/webhooks/razorpay",
        content=b"",
        headers={"X-Razorpay-Signature": "signature_123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Webhook payload cannot be empty."
    )

    service.verify.assert_not_called()


def test_razorpay_webhook_maps_gateway_failure_to_502() -> None:
    class FailingGateway:
        def verify_webhook_signature(
            self,
            payload: bytes,
            signature: str,
        ) -> bool:
            raise RazorpayProviderError(
                "Razorpay webhook verification failed."
            )

    service = RazorpayWebhookService(
        FailingGateway(),
        InMemoryWebhookReplayStore(),
    )
    client = build_client(service)

    response = client.post(
        "/webhooks/razorpay",
        content=b'{"event":"payment.captured","id":"evt_123"}',
        headers={"X-Razorpay-Signature": "signature_123"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Razorpay webhook verification failed."
    )


def test_razorpay_webhook_rejects_replayed_event() -> None:
    service = Mock()
    service.verify.return_value = RazorpayWebhookVerificationResult(
        valid=False,
        replayed=True,
    )

    client = build_client(service)

    response = client.post(
        "/webhooks/razorpay",
        content=b'{"event":"payment.captured","id":"evt_123"}',
        headers={"X-Razorpay-Signature": "signature_123"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Webhook event has already been processed."
    )


def test_razorpay_webhook_rejects_missing_event_id() -> None:
    service = Mock()
    client = build_client(service)

    response = client.post(
        "/webhooks/razorpay",
        content=b'{"event":"payment.captured"}',
        headers={"X-Razorpay-Signature": "signature_123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Webhook event ID is required."
    )

    service.verify.assert_not_called()


def test_razorpay_webhook_rejects_invalid_json() -> None:
    service = Mock()
    client = build_client(service)

    response = client.post(
        "/webhooks/razorpay",
        content=b"not-json",
        headers={"X-Razorpay-Signature": "signature_123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Webhook payload must contain valid JSON."
    )

    service.verify.assert_not_called()
