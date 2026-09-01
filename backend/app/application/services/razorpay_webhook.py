from app.application.dto.razorpay_webhook import (
    RazorpayWebhookVerificationRequest,
    RazorpayWebhookVerificationResult,
)
from app.application.ports.payment_gateway import PaymentGatewayPort
from app.application.ports.webhook_replay import WebhookReplayStore


class RazorpayWebhookService:
    """Application service for verifying external payment webhooks."""

    def __init__(
        self,
        gateway: PaymentGatewayPort,
        replay_store: WebhookReplayStore,
    ) -> None:
        self._gateway = gateway
        self._replay_store = replay_store

    def verify(
        self,
        request: RazorpayWebhookVerificationRequest,
    ) -> RazorpayWebhookVerificationResult:
        """Verify authenticity and reject previously claimed events."""
        if not request.payload:
            raise ValueError("Webhook payload cannot be empty.")

        if not request.signature.strip():
            raise ValueError("Webhook signature cannot be empty.")

        if not request.event_id.strip():
            raise ValueError("Webhook event ID cannot be empty.")

        valid = self._gateway.verify_webhook_signature(
            payload=request.payload,
            signature=request.signature,
        )

        if not valid:
            return RazorpayWebhookVerificationResult(valid=False)

        if not self._replay_store.claim(request.event_id):
            return RazorpayWebhookVerificationResult(
                valid=False,
                replayed=True,
            )

        return RazorpayWebhookVerificationResult(valid=True)
