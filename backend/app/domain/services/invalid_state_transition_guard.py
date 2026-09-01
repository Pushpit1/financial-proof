from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.state_transition_request import StateTransitionRequest


class InvalidStateTransitionGuard:
    """Prevent runtime transitions that violate the allowed state graph."""

    RULE = "invalid_state_transition"

    def __init__(
        self,
        allowed_transitions: dict[str, set[str]],
    ) -> None:
        self._allowed_transitions = {
            state: set(next_states)
            for state, next_states in allowed_transitions.items()
        }

    def evaluate(
        self,
        request: StateTransitionRequest,
    ) -> GuardianEvaluation:
        """Return whether the requested state transition is valid."""

        allowed_states = self._allowed_transitions.get(
            request.current_state,
            set(),
        )

        if request.requested_state not in allowed_states:
            return GuardianEvaluation(
                decision=GuardianDecision.BLOCK,
                rule=self.RULE,
                reason=(
                    f"Transition from '{request.current_state}' "
                    f"to '{request.requested_state}' is not allowed."
                ),
            )

        return GuardianEvaluation(
            decision=GuardianDecision.ALLOW,
            rule=self.RULE,
            reason=(
                f"Transition from '{request.current_state}' "
                f"to '{request.requested_state}' is allowed."
            ),
        )
