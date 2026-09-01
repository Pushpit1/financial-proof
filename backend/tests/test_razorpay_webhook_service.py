from app.application.dto.razorpay_webhook import (
    RazorpayWebhookVerificationRequest,
)
from app.application.ports.webhook_replay import InMemoryWebhookReplayStore
from app.application.services.razorpay_webhook import RazorpayWebhookService


class FakeGateway:
    def __init__(self, valid: bool = True) -> None:
        self.valid = valid
        self.calls = 0
        self.received_payload: bytes | None = None
        self.received_signature: str | None = None

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        self.calls += 1
        self.received_payload = payload
        self.received_signature = signature
        return self.valid


def build_service(
    gateway: FakeGateway,
) -> RazorpayWebhookService:
    return RazorpayWebhookService(
        gateway,  # type: ignore[arg-type]
        InMemoryWebhookReplayStore(),
    )


def test_verify_delegates_raw_payload_and_signature() -> None:
    gateway = FakeGateway(valid=True)
    service = build_service(gateway)

    payload = b'{"event":"payment.captured","id":"evt_123"}'

    result = service.verify(
        RazorpayWebhookVerificationRequest(
            payload=payload,
            signature="signature_123",
            event_id="evt_123",
        )
    )

    assert result.valid is True
    assert result.replayed is False
    assert gateway.calls == 1
    assert gateway.received_payload is payload
    assert gateway.received_signature == "signature_123"


def test_verify_returns_invalid_result() -> None:
    gateway = FakeGateway(valid=False)
    service = build_service(gateway)

    result = service.verify(
        RazorpayWebhookVerificationRequest(
            payload=b'{"event":"payment.captured"}',
            signature="bad_signature",
            event_id="evt_123",
        )
    )

    assert result.valid is False
    assert result.replayed is False
    assert gateway.calls == 1


def test_invalid_signature_does_not_claim_event() -> None:
    gateway = FakeGateway(valid=False)
    store = InMemoryWebhookReplayStore()
    service = RazorpayWebhookService(
        gateway,  # type: ignore[arg-type]
        store,
    )

    request = RazorpayWebhookVerificationRequest(
        payload=b'{"event":"payment.captured"}',
        signature="bad_signature",
        event_id="evt_123",
    )

    result = service.verify(request)

    assert result.valid is False
    assert store.claim("evt_123") is True


def test_duplicate_event_is_rejected_as_replay() -> None:
    gateway = FakeGateway(valid=True)
    service = build_service(gateway)

    request = RazorpayWebhookVerificationRequest(
        payload=b'{"event":"payment.captured","id":"evt_123"}',
        signature="signature_123",
        event_id="evt_123",
    )

    first = service.verify(request)
    second = service.verify(request)

    assert first.valid is True
    assert first.replayed is False

    assert second.valid is False
    assert second.replayed is True

    assert gateway.calls == 2


def test_different_event_ids_are_independent() -> None:
    gateway = FakeGateway(valid=True)
    service = build_service(gateway)

    first = service.verify(
        RazorpayWebhookVerificationRequest(
            payload=b'{"event":"payment.captured","id":"evt_1"}',
            signature="signature_1",
            event_id="evt_1",
        )
    )

    second = service.verify(
        RazorpayWebhookVerificationRequest(
            payload=b'{"event":"payment.captured","id":"evt_2"}',
            signature="signature_2",
            event_id="evt_2",
        )
    )

    assert first.valid is True
    assert second.valid is True


def test_verify_rejects_empty_payload_before_gateway() -> None:
    gateway = FakeGateway()
    service = build_service(gateway)

    try:
        service.verify(
            RazorpayWebhookVerificationRequest(
                payload=b"",
                signature="signature",
                event_id="evt_123",
            )
        )
    except ValueError as exc:
        assert str(exc) == "Webhook payload cannot be empty."
    else:
        raise AssertionError("Expected ValueError")

    assert gateway.calls == 0


def test_verify_rejects_blank_signature_before_gateway() -> None:
    gateway = FakeGateway()
    service = build_service(gateway)

    try:
        service.verify(
            RazorpayWebhookVerificationRequest(
                payload=b'{"event":"payment.captured"}',
                signature="   ",
                event_id="evt_123",
            )
        )
    except ValueError as exc:
        assert str(exc) == "Webhook signature cannot be empty."
    else:
        raise AssertionError("Expected ValueError")

    assert gateway.calls == 0


def test_verify_rejects_blank_event_id_before_gateway() -> None:
    gateway = FakeGateway()
    service = build_service(gateway)

    try:
        service.verify(
            RazorpayWebhookVerificationRequest(
                payload=b'{"event":"payment.captured"}',
                signature="signature_123",
                event_id="   ",
            )
        )
    except ValueError as exc:
        assert str(exc) == "Webhook event ID cannot be empty."
    else:
        raise AssertionError("Expected ValueError")

    assert gateway.calls == 0


def test_verify_preserves_payload_bytes_exactly() -> None:
    gateway = FakeGateway(valid=True)
    service = build_service(gateway)

    payload = (
        b'{"event":"payment.captured",'
        b'"amount":100,"currency":"INR"}\r\n'
    )

    result = service.verify(
        RazorpayWebhookVerificationRequest(
            payload=payload,
            signature="signature_123",
            event_id="evt_123",
        )
    )

    assert result.valid is True
    assert gateway.received_payload is payload
    assert gateway.received_payload == payload
