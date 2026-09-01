import pytest

from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.refund_authorization import RefundAuthorization
from app.domain.services.unauthorized_refund_guard import (
    UnauthorizedRefundGuard,
)


def test_authorized_refund_actor_is_allowed() -> None:
    guard = UnauthorizedRefundGuard()

    result = guard.evaluate(
        RefundAuthorization(
            actor_id="operator-001",
            authorized=True,
        )
    )

    assert result.decision is GuardianDecision.ALLOW
    assert result.rule == "unauthorized_refund_prevention"


def test_unauthorized_refund_actor_is_blocked() -> None:
    guard = UnauthorizedRefundGuard()

    result = guard.evaluate(
        RefundAuthorization(
            actor_id="operator-001",
            authorized=False,
        )
    )

    assert result.decision is GuardianDecision.BLOCK
    assert "not authorized" in result.reason


def test_empty_actor_id_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Refund actor ID cannot be empty",
    ):
        RefundAuthorization(
            actor_id="   ",
            authorized=True,
        )


def test_refund_authorization_is_immutable() -> None:
    authorization = RefundAuthorization(
        actor_id="operator-001",
        authorized=True,
    )

    with pytest.raises(AttributeError):
        authorization.authorized = False
