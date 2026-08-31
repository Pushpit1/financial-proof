from decimal import Decimal

from app.application.ports.payment_gateway import (
    PaymentCapture,
    PaymentGatewayPort,
    PaymentOrder,
    PaymentOrderRequest,
    PaymentRefund,
)


def test_payment_order_request_is_immutable() -> None:
    request = PaymentOrderRequest(
        amount=Decimal("100.00"),
        currency="INR",
        receipt="receipt-001",
    )

    assert request.amount == Decimal("100.00")
    assert request.currency == "INR"
    assert request.receipt == "receipt-001"

    try:
        request.currency = "USD"
    except AttributeError:
        pass
    else:
        raise AssertionError("Payment order request must be immutable.")


def test_payment_gateway_port_requires_provider_implementation() -> None:
    class FakeGateway(PaymentGatewayPort):
        def create_order(
            self,
            request: PaymentOrderRequest,
        ) -> PaymentOrder:
            return PaymentOrder(
                provider_order_id="order_123",
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
            return PaymentCapture(
                provider_payment_id=provider_payment_id,
                provider_order_id="order_123",
                amount=amount,
                currency=currency,
            )

        def refund_payment(
            self,
            provider_payment_id: str,
            amount: Decimal | None = None,
        ) -> PaymentRefund:
            refund_amount = amount or Decimal("0")
            return PaymentRefund(
                provider_refund_id="refund_123",
                provider_payment_id=provider_payment_id,
                amount=refund_amount,
                currency="INR",
            )

        def verify_webhook_signature(
            self,
            payload: bytes,
            signature: str,
        ) -> bool:
            return True

        def raw_provider_error(
            self,
            error: Exception,
        ) -> object:
            return error

    gateway = FakeGateway()

    order = gateway.create_order(
        PaymentOrderRequest(
            amount=Decimal("500.00"),
            currency="INR",
            receipt="receipt-123",
        )
    )

    assert order.provider_order_id == "order_123"
    assert order.amount == Decimal("500.00")
