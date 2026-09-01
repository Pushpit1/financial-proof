from dataclasses import dataclass


@dataclass(frozen=True)
class RefundRequest:
    """Immutable request to refund a payment."""

    amount_minor: int
    currency: str
    approval_granted: bool = False

    def __post_init__(self) -> None:
        if self.amount_minor <= 0:
            raise ValueError("Refund amount must be positive.")

        if len(self.currency) != 3:
            raise ValueError(
                "Refund currency must be a 3-letter code."
            )
