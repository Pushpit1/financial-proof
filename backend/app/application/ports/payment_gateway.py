from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class PaymentOrderRequest:
    """Application request for creating a payment order."""

    amount: Decimal
    currency: str
    receipt: str


@dataclass(frozen=True)
class PaymentOrder:
    """Application representation of a created payment order."""

    provider_order_id: str
    amount: Decimal
    currency: str
    receipt: str


@dataclass(frozen=True)
class PaymentCapture:
    """Application representation of a captured payment."""

    provider_payment_id: str
    provider_order_id: str
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class PaymentRefund:
    """Application representation of a refunded payment."""

    provider_refund_id: str
    provider_payment_id: str
    amount: Decimal
    currency: str


class PaymentGatewayPort(ABC):
    """Application boundary for external payment providers."""

    @abstractmethod
    def create_order(
        self,
        request: PaymentOrderRequest,
    ) -> PaymentOrder:
        raise NotImplementedError

    @abstractmethod
    def capture_payment(
        self,
        provider_payment_id: str,
        amount: Decimal,
        currency: str,
    ) -> PaymentCapture:
        raise NotImplementedError

    @abstractmethod
    def refund_payment(
        self,
        provider_payment_id: str,
        amount: Decimal | None = None,
    ) -> PaymentRefund:
        raise NotImplementedError

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def raw_provider_error(
        self,
        error: Exception,
    ) -> Any:
        raise NotImplementedError
