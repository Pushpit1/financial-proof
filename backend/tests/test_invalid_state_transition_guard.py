import pytest

from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.state_transition_request import StateTransitionRequest
from app.domain.services.invalid_state_transition_guard import (
    InvalidStateTransitionGuard,
)


def make_guard() -> InvalidStateTransitionGuard:
    return InvalidStateTransitionGuard(
        {
            "pending": {"authorized", "cancelled"},
            "authorized": {"captured", "cancelled"},
            "captured": {"refunded"},
            "refunded": set(),
            "cancelled": set(),
        }
    )


def test_allowed_transition_is_allowed() -> None:
    result = make_guard().evaluate(
        StateTransitionRequest(
            current_state="pending",
            requested_state="authorized",
        )
    )

    assert result.decision is GuardianDecision.ALLOW


def test_invalid_transition_is_blocked() -> None:
    result = make_guard().evaluate(
        StateTransitionRequest(
            current_state="pending",
            requested_state="refunded",
        )
    )

    assert result.decision is GuardianDecision.BLOCK
    assert result.rule == "invalid_state_transition"
    assert "not allowed" in result.reason


def test_unknown_current_state_is_blocked() -> None:
    result = make_guard().evaluate(
        StateTransitionRequest(
            current_state="unknown",
            requested_state="captured",
        )
    )

    assert result.decision is GuardianDecision.BLOCK


def test_terminal_state_cannot_transition() -> None:
    result = make_guard().evaluate(
        StateTransitionRequest(
            current_state="refunded",
            requested_state="captured",
        )
    )

    assert result.decision is GuardianDecision.BLOCK


@pytest.mark.parametrize(
    ("current_state", "requested_state"),
    [
        ("", "pending"),
        ("pending", ""),
    ],
)
def test_empty_state_is_rejected(
    current_state: str,
    requested_state: str,
) -> None:
    with pytest.raises(ValueError):
        StateTransitionRequest(
            current_state=current_state,
            requested_state=requested_state,
        )


def test_transition_request_is_immutable() -> None:
    request = StateTransitionRequest(
        current_state="pending",
        requested_state="authorized",
    )

    with pytest.raises(AttributeError):
        request.current_state = "captured"
