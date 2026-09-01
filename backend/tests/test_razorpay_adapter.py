from decimal import Decimal

import pytest

from app.application.ports.payment_gateway import PaymentOrderRequest
from app.infrastructure.razorpay_adapter import (
    RazorpayAdapterError,
    RazorpayPaymentGateway,
    RazorpayProviderError,
)
from app.infrastructure.razorpay_settings import RazorpaySettings


class FakeOrderAPI:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def create(self, data: dict) -> dict:
        self.calls.append(data)

        if self.error is not None:
            raise self.error

        return self.response


class FakeRazorpayClient:
    def __init__(self, order_api: FakeOrderAPI) -> None:
        self.order = order_api
        self.payment = object()


def gateway_with_order_api(order_api: FakeOrderAPI) -> RazorpayPaymentGateway:
    settings = RazorpaySettings(
        key_id="rzp_test_key",
        key_secret="test_secret",
    )

    return RazorpayPaymentGateway(
        settings,
        client=FakeRazorpayClient(order_api),
    )


def test_razorpay_adapter_accepts_valid_configuration() -> None:
    settings = RazorpaySettings(
        key_id="rzp_test_key",
        key_secret="test_secret",
    )

    gateway = RazorpayPaymentGateway(
        settings,
        client=FakeRazorpayClient(FakeOrderAPI()),
    )

    assert gateway is not None


def test_razorpay_adapter_uses_injected_client() -> None:
    settings = RazorpaySettings(
        key_id="rzp_test_key",
        key_secret="test_secret",
    )
    client = FakeRazorpayClient(FakeOrderAPI())

    gateway = RazorpayPaymentGateway(
        settings,
        client=client,
    )

    assert gateway.client is client


def test_create_order_converts_rupees_to_paise() -> None:
    order_api = FakeOrderAPI(
        response={
            "id": "order_ABC123",
            "amount": 50000,
            "currency": "INR",
            "receipt": "receipt-123",
        }
    )
    gateway = gateway_with_order_api(order_api)

    result = gateway.create_order(
        PaymentOrderRequest(
            amount=Decimal("500.00"),
            currency="INR",
            receipt="receipt-123",
        )
    )

    assert order_api.calls == [
        {
            "amount": 50000,
            "currency": "INR",
            "receipt": "receipt-123",
        }
    ]

    assert result.provider_order_id == "order_ABC123"
    assert result.amount == Decimal("500.00")
    assert result.currency == "INR"
    assert result.receipt == "receipt-123"


def test_create_order_rejects_zero_amount() -> None:
    gateway = gateway_with_order_api(FakeOrderAPI())

    with pytest.raises(
        ValueError,
        match="amount must be greater than zero",
    ):
        gateway.create_order(
            PaymentOrderRequest(
                amount=Decimal("0"),
                currency="INR",
                receipt="receipt-123",
            )
        )


def test_create_order_rejects_more_than_two_decimal_places() -> None:
    gateway = gateway_with_order_api(FakeOrderAPI())

    with pytest.raises(
        ValueError,
        match="at most two decimal places",
    ):
        gateway.create_order(
            PaymentOrderRequest(
                amount=Decimal("10.001"),
                currency="INR",
                receipt="receipt-123",
            )
        )


def test_create_order_rejects_empty_currency() -> None:
    gateway = gateway_with_order_api(FakeOrderAPI())

    with pytest.raises(
        ValueError,
        match="currency cannot be empty",
    ):
        gateway.create_order(
            PaymentOrderRequest(
                amount=Decimal("10.00"),
                currency="",
                receipt="receipt-123",
            )
        )


def test_create_order_rejects_empty_receipt() -> None:
    gateway = gateway_with_order_api(FakeOrderAPI())

    with pytest.raises(
        ValueError,
        match="receipt cannot be empty",
    ):
        gateway.create_order(
            PaymentOrderRequest(
                amount=Decimal("10.00"),
                currency="INR",
                receipt="",
            )
        )


def test_create_order_maps_provider_failure() -> None:
    gateway = gateway_with_order_api(
        FakeOrderAPI(error=RuntimeError("provider unavailable"))
    )

    with pytest.raises(
        RazorpayProviderError,
        match="order creation failed",
    ):
        gateway.create_order(
            PaymentOrderRequest(
                amount=Decimal("10.00"),
                currency="INR",
                receipt="receipt-123",
            )
        )


def test_create_order_rejects_missing_provider_order_id() -> None:
    gateway = gateway_with_order_api(
        FakeOrderAPI(
            response={
                "amount": 1000,
                "currency": "INR",
                "receipt": "receipt-123",
            }
        )
    )

    with pytest.raises(
        RazorpayProviderError,
        match="missing a valid order ID",
    ):
        gateway.create_order(
            PaymentOrderRequest(
                amount=Decimal("10.00"),
                currency="INR",
                receipt="receipt-123",
            )
        )


def test_create_order_rejects_mismatched_provider_amount() -> None:
    gateway = gateway_with_order_api(
        FakeOrderAPI(
            response={
                "id": "order_ABC123",
                "amount": 999,
                "currency": "INR",
                "receipt": "receipt-123",
            }
        )
    )

    with pytest.raises(
        RazorpayProviderError,
        match="amount does not match",
    ):
        gateway.create_order(
            PaymentOrderRequest(
                amount=Decimal("10.00"),
                currency="INR",
                receipt="receipt-123",
            )
        )


def test_create_order_rejects_mismatched_provider_currency() -> None:
    gateway = gateway_with_order_api(
        FakeOrderAPI(
            response={
                "id": "order_ABC123",
                "amount": 1000,
                "currency": "USD",
                "receipt": "receipt-123",
            }
        )
    )

    with pytest.raises(
        RazorpayProviderError,
        match="currency does not match",
    ):
        gateway.create_order(
            PaymentOrderRequest(
                amount=Decimal("10.00"),
                currency="INR",
                receipt="receipt-123",
            )
        )


def test_create_order_rejects_mismatched_provider_receipt() -> None:
    gateway = gateway_with_order_api(
        FakeOrderAPI(
            response={
                "id": "order_ABC123",
                "amount": 1000,
                "currency": "INR",
                "receipt": "different-receipt",
            }
        )
    )

    with pytest.raises(
        RazorpayProviderError,
        match="receipt does not match",
    ):
        gateway.create_order(
            PaymentOrderRequest(
                amount=Decimal("10.00"),
                currency="INR",
                receipt="receipt-123",
            )
        )


def test_provider_error_is_an_adapter_error() -> None:
    assert issubclass(
        RazorpayProviderError,
        RazorpayAdapterError,
    )
class FakePaymentAPI:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[str, int, str]] = []

    def capture(
        self,
        payment_id: str,
        amount: int,
        currency: str,
    ) -> dict:
        self.calls.append(
            (payment_id, amount, currency)
        )

        if self.error is not None:
            raise self.error

        return self.response


class FakeClientWithPayment:
    def __init__(self, payment_api) -> None:
        self.order = FakeOrderAPI()
        self.payment = payment_api


def test_capture_payment_maps_successful_response() -> None:
    from decimal import Decimal

    payment_api = FakePaymentAPI(
        response={
            "id": "pay_ABC123",
            "order_id": "order_ABC123",
            "amount": 50000,
            "currency": "INR",
        }
    )

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithPayment(payment_api),
    )

    result = gateway.capture_payment(
        provider_payment_id="pay_ABC123",
        amount=Decimal("500.00"),
        currency="INR",
    )

    assert payment_api.calls == [
        ("pay_ABC123", 50000, "INR")
    ]

    assert result.provider_payment_id == "pay_ABC123"
    assert result.provider_order_id == "order_ABC123"
    assert result.amount == Decimal("500.00")
    assert result.currency == "INR"


def test_capture_payment_maps_provider_failure() -> None:
    from decimal import Decimal

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithPayment(
            FakePaymentAPI(
                error=RuntimeError("provider unavailable")
            )
        ),
    )

    with pytest.raises(
        RazorpayProviderError,
        match="payment capture failed",
    ):
        gateway.capture_payment(
            provider_payment_id="pay_ABC123",
            amount=Decimal("500.00"),
            currency="INR",
        )


def test_capture_payment_rejects_empty_payment_id() -> None:
    from decimal import Decimal

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithPayment(FakePaymentAPI()),
    )

    with pytest.raises(
        ValueError,
        match="payment ID cannot be empty",
    ):
        gateway.capture_payment(
            provider_payment_id="",
            amount=Decimal("500.00"),
            currency="INR",
        )


def test_capture_payment_rejects_mismatched_amount() -> None:
    from decimal import Decimal

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithPayment(
            FakePaymentAPI(
                response={
                    "id": "pay_ABC123",
                    "order_id": "order_ABC123",
                    "amount": 49999,
                    "currency": "INR",
                }
            )
        ),
    )

    with pytest.raises(
        RazorpayProviderError,
        match="amount does not match",
    ):
        gateway.capture_payment(
            provider_payment_id="pay_ABC123",
            amount=Decimal("500.00"),
            currency="INR",
        )


def test_capture_payment_rejects_missing_order_id() -> None:
    from decimal import Decimal

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithPayment(
            FakePaymentAPI(
                response={
                    "id": "pay_ABC123",
                    "amount": 50000,
                    "currency": "INR",
                }
            )
        ),
    )

    with pytest.raises(
        RazorpayProviderError,
        match="missing a valid order ID",
    ):
        gateway.capture_payment(
            provider_payment_id="pay_ABC123",
            amount=Decimal("500.00"),
            currency="INR",
        )

class FakeRefundPaymentAPI:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[str, dict | None]] = []

    def capture(
        self,
        payment_id: str,
        amount: int,
        currency: str,
    ) -> dict:
        raise NotImplementedError

    def refund(
        self,
        payment_id: str,
        data: dict | None = None,
    ) -> dict:
        self.calls.append((payment_id, data))

        if self.error is not None:
            raise self.error

        return self.response


class FakeClientWithRefund:
    def __init__(self, payment_api) -> None:
        self.order = FakeOrderAPI()
        self.payment = payment_api


def test_refund_payment_maps_partial_refund() -> None:
    from decimal import Decimal

    payment_api = FakeRefundPaymentAPI(
        response={
            "id": "rfnd_ABC123",
            "payment_id": "pay_ABC123",
            "amount": 25000,
            "currency": "INR",
        }
    )

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithRefund(payment_api),
    )

    result = gateway.refund_payment(
        provider_payment_id="pay_ABC123",
        amount=Decimal("250.00"),
    )

    assert payment_api.calls == [
        ("pay_ABC123", {"amount": 25000})
    ]

    assert result.provider_refund_id == "rfnd_ABC123"
    assert result.provider_payment_id == "pay_ABC123"
    assert result.amount == Decimal("250.00")
    assert result.currency == "INR"


def test_refund_payment_supports_full_refund_without_amount() -> None:
    from decimal import Decimal

    payment_api = FakeRefundPaymentAPI(
        response={
            "id": "rfnd_FULL123",
            "payment_id": "pay_ABC123",
            "amount": 50000,
            "currency": "INR",
        }
    )

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithRefund(payment_api),
    )

    result = gateway.refund_payment(
        provider_payment_id="pay_ABC123",
    )

    assert payment_api.calls == [
        ("pay_ABC123", None)
    ]

    assert result.provider_refund_id == "rfnd_FULL123"
    assert result.provider_payment_id == "pay_ABC123"
    assert result.amount == Decimal("500.00")
    assert result.currency == "INR"


def test_refund_payment_maps_provider_failure() -> None:
    from decimal import Decimal

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithRefund(
            FakeRefundPaymentAPI(
                error=RuntimeError("provider unavailable")
            )
        ),
    )

    with pytest.raises(
        RazorpayProviderError,
        match="payment refund failed",
    ):
        gateway.refund_payment(
            provider_payment_id="pay_ABC123",
            amount=Decimal("100.00"),
        )


def test_refund_payment_rejects_empty_payment_id() -> None:
    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithRefund(
            FakeRefundPaymentAPI()
        ),
    )

    with pytest.raises(
        ValueError,
        match="payment ID cannot be empty",
    ):
        gateway.refund_payment(
            provider_payment_id="",
        )


def test_refund_payment_rejects_invalid_amount() -> None:
    from decimal import Decimal

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithRefund(
            FakeRefundPaymentAPI()
        ),
    )

    with pytest.raises(
        ValueError,
        match="at most two decimal places",
    ):
        gateway.refund_payment(
            provider_payment_id="pay_ABC123",
            amount=Decimal("10.001"),
        )


def test_refund_payment_rejects_mismatched_provider_amount() -> None:
    from decimal import Decimal

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=FakeClientWithRefund(
            FakeRefundPaymentAPI(
                response={
                    "id": "rfnd_ABC123",
                    "payment_id": "pay_ABC123",
                    "amount": 999,
                    "currency": "INR",
                }
            )
        ),
    )

    with pytest.raises(
        RazorpayProviderError,
        match="amount does not match",
    ):
        gateway.refund_payment(
            provider_payment_id="pay_ABC123",
            amount=Decimal("10.00"),
        )


class FakeWebhookUtility:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, str, str]] = []

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
    ) -> None:
        self.calls.append((payload, signature, secret))

        if self.error is not None:
            raise self.error


class FakeClientWithWebhookUtility:
    def __init__(self, utility: FakeWebhookUtility) -> None:
        self.order = FakeOrderAPI()
        self.payment = object()
        self.utility = utility


def test_verify_webhook_signature_passes_raw_payload_and_secret() -> None:
    utility = FakeWebhookUtility()
    client = FakeClientWithWebhookUtility(utility)

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=client,
    )

    payload = b'{"event":"payment.captured","amount":100}\r\n'

    result = gateway.verify_webhook_signature(
        payload=payload,
        signature="signature_123",
    )

    assert result is True
    assert utility.calls == [
        (
            payload.decode("utf-8"),
            "signature_123",
            "test_secret",
        )
    ]


def test_verify_webhook_signature_rejects_empty_payload_before_provider() -> None:
    utility = FakeWebhookUtility()
    client = FakeClientWithWebhookUtility(utility)

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=client,
    )

    with pytest.raises(
        ValueError,
        match="Webhook payload cannot be empty",
    ):
        gateway.verify_webhook_signature(
            payload=b"",
            signature="signature_123",
        )

    assert utility.calls == []


def test_verify_webhook_signature_rejects_blank_signature_before_provider() -> None:
    utility = FakeWebhookUtility()
    client = FakeClientWithWebhookUtility(utility)

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=client,
    )

    with pytest.raises(
        ValueError,
        match="Webhook signature cannot be empty",
    ):
        gateway.verify_webhook_signature(
            payload=b'{"event":"payment.captured"}',
            signature="   ",
        )

    assert utility.calls == []


def test_verify_webhook_signature_returns_false_on_provider_rejection() -> None:
    utility = FakeWebhookUtility(
        error=RuntimeError("invalid signature"),
    )
    client = FakeClientWithWebhookUtility(utility)

    gateway = RazorpayPaymentGateway(
        RazorpaySettings(
            key_id="rzp_test_key",
            key_secret="test_secret",
        ),
        client=client,
    )

    result = gateway.verify_webhook_signature(
        payload=b'{"event":"payment.captured"}',
        signature="invalid_signature",
    )

    assert result is False
    assert utility.calls == [
        (
            '{"event":"payment.captured"}',
            "invalid_signature",
            "test_secret",
        )
    ]
