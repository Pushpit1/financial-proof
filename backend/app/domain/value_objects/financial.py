from dataclasses import dataclass
from datetime import date
from decimal import Decimal


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