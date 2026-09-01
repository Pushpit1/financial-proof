from collections.abc import Iterable

from app.domain.models.payment import Payment
from app.domain.models.payment_transition import PaymentTransition
from app.domain.services.payment_state_machine import (
    PaymentStateMachine,
)


class ReplayConsistencyError(ValueError):
    """Raised when recorded transition history is inconsistent."""


class PaymentTransitionReplayService:
    """Reconstruct payment state from recorded transitions."""

    @staticmethod
    def replay(
        initial_state: Payment,
        transitions: Iterable[PaymentTransition],
    ) -> Payment:
        current = initial_state

        for transition in transitions:
            if transition.payment_id != current.id:
                raise ReplayConsistencyError(
                    "Transition belongs to a different payment."
                )

            if transition.from_state != current.state:
                raise ReplayConsistencyError(
                    "Transition from_state does not match current state."
                )

            reconstructed = PaymentStateMachine.transition(
                current,
                transition.event,
            )

            if reconstructed.state != transition.to_state:
                raise ReplayConsistencyError(
                    "Recorded transition does not match "
                    "the deterministic state machine."
                )

            current = reconstructed

        return current
