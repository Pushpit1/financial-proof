from enum import StrEnum


class OrderState(StrEnum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentState(StrEnum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentEvent(StrEnum):
    AUTHORIZE = "authorize"
    CAPTURE = "capture"
    REFUND = "refund"
    FAIL = "fail"
    CANCEL = "cancel"
