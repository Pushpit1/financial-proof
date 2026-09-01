from dataclasses import dataclass
from enum import StrEnum


class FinancialOperation(StrEnum):
    """Financial operations subject to runtime authorization."""

    REFUND = "refund"
    CHARGE = "charge"
    FULFILLMENT = "fulfillment"


@dataclass(frozen=True)
class ContractAuthorizationRequest:
    """Immutable request for contract-aware authorization."""

    actor_id: str
    operation: FinancialOperation
    actor_authorized: bool
    operation_authorized: bool

    def __post_init__(self) -> None:
        if not self.actor_id.strip():
            raise ValueError("Actor ID cannot be empty.")
