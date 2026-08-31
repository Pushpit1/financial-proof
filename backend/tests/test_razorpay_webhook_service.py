from app.application.dto.razorpay_webhook import (
    RazorpayWebhookVerificationRequest,
)
from app.application.services.razorpay_webhook import (
    RazorpayWebhookService,
)


class FakeGateway:
    def __init__(self, valid: bool = True) -> None:
        self.valid = valid
        self.received_payload: bytes | None = None
        self.received_signature: str | None = None

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        self.received_payload = payload
        self.received_signature = signature
        return self.valid


def test_verify_delegates_raw_payload_and_signature() -> None:
    gateway = FakeGateway(valid=True)
    service = RazorpayWebhookService(gateway)  # type: ignore[arg-type]

    payload = b'{"event":"payment.captured","id":"evt_123"}'

    result = service.verify(
        RazorpayWebhookVerificationRequest(
            payload=payload,
            signature="signature_123",
        )
    )

    assert result.valid is True
    assert gateway.received_payload == payload
    assert gateway.received_signature == "signature_123"


def test_verify_returns_invalid_result() -> None:
    gateway = FakeGateway(valid=False)
    service = RazorpayWebhookService(gateway)  # type: ignore[arg-type]

    result = service.verify(
        RazorpayWebhookVerificationRequest(
            payload=b'{"event":"payment.captured"}',
            signature="bad_signature",
        )
    )

    assert result.valid is False


def test_verify_rejects_empty_payload() -> None:
    gateway = FakeGateway()
    service = RazorpayWebhookService(gateway)  # type: ignore[arg-type]

    try:
        service.verify(
            RazorpayWebhookVerificationRequest(
                payload=b"",
                signature="signature",
            )
        )
    except ValueError as exc:
        assert str(exc) == "Webhook payload cannot be empty."
    else:
        raise AssertionError("Expected ValueError")


def test_verify_rejects_empty_signature() -> None:
    gateway = FakeGateway()
    service = RazorpayWebhookService(gateway)  # type: ignore[arg-type]

    try:
        service.verify(
            RazorpayWebhookVerificationRequest(
                payload=b'{"event":"payment.captured"}',
                signature="   ",
            )
        )
    except ValueError as exc:
        assert str(exc) == "Webhook signature cannot be empty."
    else:
        raise AssertionError("Expected ValueError")
