from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.domain.enums.financial import (
    ContractAuthorizationAction,
    ContractIdempotencyMode,
    ContractOperator,
    ContractRuleType,
    ContractState,
    ContractTimeRelation,
    ContractTransitionTrigger,
)


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative.")

        normalized_currency = self.currency.upper()

        if len(normalized_currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code.")

        if not normalized_currency.isalpha():
            raise ValueError("Currency must contain only letters.")

        object.__setattr__(self, "currency", normalized_currency)


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
class ContractCondition:
    """Immutable structured condition used by a financial contract."""

    field: str
    operator: ContractOperator
    value: Any = None

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("Contract condition field cannot be empty.")

        if self.field != self.field.strip():
            raise ValueError(
                "Contract condition field cannot contain surrounding whitespace."
            )

        if self.operator in (
            ContractOperator.EXISTS,
            ContractOperator.NOT_EXISTS,
        ):
            if self.value is not None:
                raise ValueError(
                    "Existence conditions cannot define a value."
                )
            return

        if self.value is None:
            raise ValueError(
                "Contract condition value cannot be empty."
            )

        if self.operator in (
            ContractOperator.IN,
            ContractOperator.NOT_IN,
        ):
            if not isinstance(
                self.value,
                (tuple, list, set, frozenset),
            ):
                raise ValueError(
                    "Membership condition value must be a collection."
                )

            if not self.value:
                raise ValueError(
                    "Membership condition value cannot be empty."
                )


@dataclass(frozen=True)
class ContractRule:
    """Immutable deterministic rule declared by a financial contract."""

    name: str
    condition: ContractCondition
    rule_type: ContractRuleType
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Contract rule name cannot be empty.")


@dataclass(frozen=True)
class ContractField:
    """A typed input or output declared by a financial contract."""

    name: str
    data_type: str
    required: bool = True
    description: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Contract field name cannot be empty.")

        if not self.data_type.strip():
            raise ValueError(
                "Contract field data type cannot be empty."
            )

        if self.name != self.name.strip():
            raise ValueError(
                "Contract field name cannot contain surrounding whitespace."
            )

        if self.data_type != self.data_type.strip():
            raise ValueError(
                "Contract field data type cannot contain surrounding whitespace."
            )

        if self.description is not None and not self.description.strip():
            raise ValueError(
                "Contract field description cannot be empty."
            )


@dataclass(frozen=True)
class FinancialConstraint:
    """Immutable financial-specific constraint declared by a contract."""

    field: str
    operator: ContractOperator
    value: Decimal
    currency: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError(
                "Financial constraint field cannot be empty."
            )

        if self.field != self.field.strip():
            raise ValueError(
                "Financial constraint field cannot contain surrounding whitespace."
            )

        if self.operator in (
            ContractOperator.EXISTS,
            ContractOperator.NOT_EXISTS,
            ContractOperator.IN,
            ContractOperator.NOT_IN,
        ):
            raise ValueError(
                "Financial constraints require a numeric comparison operator."
            )

        if self.currency is not None:
            normalized_currency = self.currency.upper()

            if len(normalized_currency) != 3:
                raise ValueError(
                    "Financial constraint currency must be a "
                    "3-letter ISO code."
                )

            if not normalized_currency.isalpha():
                raise ValueError(
                    "Financial constraint currency must contain "
                    "only letters."
                )

            object.__setattr__(
                self,
                "currency",
                normalized_currency,
            )


@dataclass(frozen=True)
class ContractAuthorization:
    """Immutable authorization requirement for a contract operation."""

    actor: str
    action: ContractAuthorizationAction
    resource: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ValueError(
                "Contract authorization actor cannot be empty."
            )

        if not self.resource.strip():
            raise ValueError(
                "Contract authorization resource cannot be empty."
            )


@dataclass(frozen=True)
class ContractTemporalRule:
    """Immutable temporal restriction for a contract."""

    field: str
    relation: ContractTimeRelation
    start: datetime
    end: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError(
                "Contract temporal rule field cannot be empty."
            )

        if self.field != self.field.strip():
            raise ValueError(
                "Contract temporal rule field cannot contain surrounding whitespace."
            )

        if (
            self.relation == ContractTimeRelation.BETWEEN
            and self.end is None
        ):
            raise ValueError(
                "Between temporal rules require an end timestamp."
            )

        if (
            self.end is not None
            and self.relation == ContractTimeRelation.BETWEEN
            and self.end < self.start
        ):
            raise ValueError(
                "Temporal rule end cannot precede its start."
            )

        if (
            self.end is not None
            and self.relation != ContractTimeRelation.BETWEEN
        ):
            raise ValueError(
                "Only between temporal rules may define an end timestamp."
            )


@dataclass(frozen=True)
class ContractIdempotencyPolicy:
    """Immutable idempotency policy declared by a contract."""

    mode: ContractIdempotencyMode
    key_field: str | None = None
    ttl_seconds: int | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.mode == ContractIdempotencyMode.DISABLED:
            if self.key_field is not None:
                raise ValueError(
                    "Disabled idempotency cannot define a key field."
                )

            if self.ttl_seconds is not None:
                raise ValueError(
                    "Disabled idempotency cannot define a TTL."
                )

            return

        if self.key_field is None or not self.key_field.strip():
            raise ValueError(
                "Enabled idempotency requires a key field."
            )

        if self.key_field != self.key_field.strip():
            raise ValueError(
                "Idempotency key field cannot contain surrounding whitespace."
            )

        if self.ttl_seconds is not None and self.ttl_seconds <= 0:
            raise ValueError(
                "Idempotency TTL must be greater than zero."
            )


@dataclass(frozen=True)
class ContractStateTransition:
    """Immutable allowed transition between contract states."""

    from_state: ContractState
    to_state: ContractState
    trigger: ContractTransitionTrigger
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.from_state == self.to_state:
            raise ValueError(
                "Contract state transition must change state."
            )
