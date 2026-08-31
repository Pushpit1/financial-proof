from app.application.dto.razorpay_webhook import (
    RazorpayWebhookVerificationRequest,
    RazorpayWebhookVerificationResult,
)
from app.application.ports.payment_gateway import PaymentGatewayPort


class RazorpayWebhookService:
    """Application service for verifying external payment webhooks."""

    def __init__(
        self,
        gateway: PaymentGatewayPort,
    ) -> None:
        self._gateway = gateway

    def verify(
        self,
        request: RazorpayWebhookVerificationRequest,
    ) -> RazorpayWebhookVerificationResult:
        """Verify a webhook using the payment gateway boundary."""
        if not request.payload:
            raise ValueError("Webhook payload cannot be empty.")

        if not request.signature.strip():
            raise ValueError("Webhook signature cannot be empty.")

        valid = self._gateway.verify_webhook_signature(
            payload=request.payload,
            signature=request.signature,
        )

        return RazorpayWebhookVerificationResult(valid=valid)
