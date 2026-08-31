from decimal import Decimal
from typing import Any, Protocol

from app.application.ports.payment_gateway import (
    PaymentCapture,
    PaymentGatewayPort,
    PaymentOrder,
    PaymentOrderRequest,
    PaymentRefund,
)
from app.infrastructure.razorpay_settings import RazorpaySettings


class RazorpayOrderAPIProtocol(Protocol):
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        ...


class RazorpayUtilityAPIProtocol(Protocol):
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
    ) -> Any:
        ...


class RazorpayPaymentAPIProtocol(Protocol):
    def capture(
        self,
        payment_id: str,
        amount: int,
        currency: str,
    ) -> dict[str, Any]:
        ...

    def refund(
        self,
        payment_id: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...


class RazorpayClientProtocol(Protocol):
    @property
    def order(self) -> RazorpayOrderAPIProtocol:
        ...

    @property
    def payment(self) -> RazorpayPaymentAPIProtocol:
        ...

    @property
    def utility(self) -> RazorpayUtilityAPIProtocol:
        ...


class RazorpayAdapterError(Exception):
    """Base error raised by the Razorpay adapter."""


class RazorpayConfigurationError(RazorpayAdapterError):
    """Raised when Razorpay configuration is invalid."""


class RazorpayProviderError(RazorpayAdapterError):
    """Raised when Razorpay rejects or cannot process an operation."""


class RazorpayPaymentGateway(PaymentGatewayPort):
    """Razorpay implementation of the application payment gateway port."""

    def __init__(
        self,
        settings: RazorpaySettings,
        client: RazorpayClientProtocol | None = None,
    ) -> None:
        self._settings = settings

        if not settings.key_id.strip():
            raise RazorpayConfigurationError(
                "Razorpay key ID cannot be empty."
            )

        if not settings.key_secret.strip():
            raise RazorpayConfigurationError(
                "Razorpay key secret cannot be empty."
            )

        if settings.timeout_seconds <= 0:
            raise RazorpayConfigurationError(
                "Razorpay timeout must be greater than zero."
            )

        self._client = client or self._build_client()

    def _build_client(self) -> RazorpayClientProtocol:
        """Construct the real Razorpay SDK client at the infrastructure boundary."""
        try:
            import razorpay
        except ImportError as exc:
            raise RazorpayConfigurationError(
                "The Razorpay SDK is not installed."
            ) from exc

        return razorpay.Client(
            auth=(
                self._settings.key_id,
                self._settings.key_secret,
            )
        )

    @property
    def client(self) -> RazorpayClientProtocol:
        return self._client

    @staticmethod
    def _amount_to_paise(amount: Decimal) -> int:
        if amount <= Decimal("0"):
            raise ValueError("Payment amount must be greater than zero.")

        paise = amount * Decimal("100")

        if paise != paise.to_integral_value():
            raise ValueError(
                "Payment amount must have at most two decimal places."
            )

        return int(paise)

    def create_order(
        self,
        request: PaymentOrderRequest,
    ) -> PaymentOrder:
        if not request.currency.strip():
            raise ValueError("Payment currency cannot be empty.")

        if not request.receipt.strip():
            raise ValueError("Payment receipt cannot be empty.")

        payload = {
            "amount": self._amount_to_paise(request.amount),
            "currency": request.currency,
            "receipt": request.receipt,
        }

        try:
            response = self._client.order.create(payload)
        except Exception as exc:
            raise RazorpayProviderError(
                "Razorpay order creation failed."
            ) from exc

        provider_order_id = response.get("id")

        if not isinstance(provider_order_id, str) or not provider_order_id.strip():
            raise RazorpayProviderError(
                "Razorpay order response is missing a valid order ID."
            )

        if response.get("amount") != payload["amount"]:
            raise RazorpayProviderError(
                "Razorpay order response amount does not match the request."
            )

        if response.get("currency") != request.currency:
            raise RazorpayProviderError(
                "Razorpay order response currency does not match the request."
            )

        if response.get("receipt") != request.receipt:
            raise RazorpayProviderError(
                "Razorpay order response receipt does not match the request."
            )

        return PaymentOrder(
            provider_order_id=provider_order_id,
            amount=request.amount,
            currency=request.currency,
            receipt=request.receipt,
        )

    def capture_payment(
        self,
        provider_payment_id: str,
        amount: Decimal,
        currency: str,
    ) -> PaymentCapture:
        if not provider_payment_id.strip():
            raise ValueError("Provider payment ID cannot be empty.")

        if not currency.strip():
            raise ValueError("Payment currency cannot be empty.")

        paise = self._amount_to_paise(amount)

        try:
            response = self._client.payment.capture(
                provider_payment_id,
                paise,
                currency,
            )
        except Exception as exc:
            raise RazorpayProviderError(
                "Razorpay payment capture failed."
            ) from exc

        response_payment_id = response.get("id")
        response_order_id = response.get("order_id")
        response_amount = response.get("amount")
        response_currency = response.get("currency")

        if (
            not isinstance(response_payment_id, str)
            or not response_payment_id.strip()
        ):
            raise RazorpayProviderError(
                "Razorpay capture response is missing a valid payment ID."
            )

        if (
            not isinstance(response_order_id, str)
            or not response_order_id.strip()
        ):
            raise RazorpayProviderError(
                "Razorpay capture response is missing a valid order ID."
            )

        if response_amount != paise:
            raise RazorpayProviderError(
                "Razorpay capture response amount does not match the request."
            )

        if response_currency != currency:
            raise RazorpayProviderError(
                "Razorpay capture response currency does not match the request."
            )

        return PaymentCapture(
            provider_payment_id=response_payment_id,
            provider_order_id=response_order_id,
            amount=amount,
            currency=currency,
        )

    def refund_payment(
        self,
        provider_payment_id: str,
        amount: Decimal | None = None,
    ) -> PaymentRefund:
        if not provider_payment_id.strip():
            raise ValueError("Provider payment ID cannot be empty.")

        paise: int | None = None

        if amount is not None:
            paise = self._amount_to_paise(amount)

        payload = None if paise is None else {"amount": paise}

        try:
            response = self._client.payment.refund(
                provider_payment_id,
                payload,
            )
        except Exception as exc:
            raise RazorpayProviderError(
                "Razorpay payment refund failed."
            ) from exc

        response_refund_id = response.get("id")
        response_payment_id = response.get("payment_id")
        response_amount = response.get("amount")

        if (
            not isinstance(response_refund_id, str)
            or not response_refund_id.strip()
        ):
            raise RazorpayProviderError(
                "Razorpay refund response is missing a valid refund ID."
            )

        if (
            not isinstance(response_payment_id, str)
            or not response_payment_id.strip()
        ):
            raise RazorpayProviderError(
                "Razorpay refund response is missing a valid payment ID."
            )

        if paise is not None and response_amount != paise:
            raise RazorpayProviderError(
                "Razorpay refund response amount does not match the request."
            )

        response_currency = response.get("currency")

        if response_currency is not None and not isinstance(
            response_currency,
            str,
        ):
            raise RazorpayProviderError(
                "Razorpay refund response currency is invalid."
            )

        return PaymentRefund(
            provider_refund_id=response_refund_id,
            provider_payment_id=response_payment_id,
            amount=(
                amount
                if amount is not None
                else Decimal(response_amount) / Decimal("100")
            ),
            currency=response_currency or self._settings.default_currency,
        )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify a Razorpay webhook signature against the raw payload."""
        if not payload:
            raise ValueError("Webhook payload cannot be empty.")

        if not signature.strip():
            raise ValueError("Webhook signature cannot be empty.")

        try:
            self._client.utility.verify_webhook_signature(
                payload.decode("utf-8"),
                signature,
                self._settings.key_secret,
            )
        except Exception:
            return False

        return True

    def raw_provider_error(
        self,
        error: Exception,
    ) -> Any:
        return error
