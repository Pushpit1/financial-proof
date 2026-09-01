from dataclasses import dataclass


@dataclass(frozen=True)
class StateTransitionRequest:
    """Immutable request to move an entity between runtime states."""

    current_state: str
    requested_state: str

    def __post_init__(self) -> None:
        if not self.current_state.strip():
            raise ValueError("Current state cannot be empty.")

        if not self.requested_state.strip():
            raise ValueError("Requested state cannot be empty.")
