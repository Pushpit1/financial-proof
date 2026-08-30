from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.enums.financial import ContractRuleType


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative.")

        if len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code.")


@dataclass(frozen=True)
class FinancialPeriod:
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("Period end date cannot precede start date.")


@dataclass(frozen=True)
class ConfidenceScore:
    value: Decimal

    def __post_init__(self) -> None:
        if not Decimal("0") <= self.value <= Decimal("1"):
            raise ValueError("Confidence score must be between 0 and 1.")


@dataclass(frozen=True)
class ContractRule:
    """Immutable rule declared by a financial contract."""

    name: str
    expression: str
    rule_type: ContractRuleType
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Contract rule name cannot be empty.")

        if not self.expression.strip():
            raise ValueError(
                "Contract rule expression cannot be empty."
            )
