from dataclasses import dataclass


@dataclass(frozen=True)
class RazorpayWebhookVerificationRequest:
    """Application request for verifying a Razorpay webhook."""

    payload: bytes
    signature: str


@dataclass(frozen=True)
class RazorpayWebhookVerificationResult:
    """Deterministic result of webhook signature verification."""

    valid: bool
