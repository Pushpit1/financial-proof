from dataclasses import dataclass


@dataclass(frozen=True)
class RefundAuthorization:
    """Immutable authorization context for a refund operation."""

    actor_id: str
    authorized: bool

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("Refund actor ID cannot be empty.")
