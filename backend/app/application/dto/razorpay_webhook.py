from dataclasses import dataclass


@dataclass(frozen=True)
class RazorpayWebhookVerificationRequest:
    """Application request for verifying a Razorpay webhook."""

    payload: bytes
    signature: str
    event_id: str


@dataclass(frozen=True)
class RazorpayWebhookVerificationResult:
    """Deterministic result of webhook verification."""

    valid: bool
    replayed: bool = False
