from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ContractViolation:
    """A deterministic contract evaluation violation."""

    rule: str
    message: str
    field: str | None = None
    id: UUID = dataclass_field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.rule.strip():
            raise ValueError("Contract violation rule cannot be empty.")

        if not self.message.strip():
            raise ValueError(
                "Contract violation message cannot be empty."
            )

        if self.field is not None and not self.field.strip():
            raise ValueError(
                "Contract violation field cannot be empty."
            )


@dataclass(frozen=True)
class ContractEvaluationResult:
    """Immutable result of evaluating a financial contract."""

    contract_id: UUID
    passed: bool
    violations: tuple[ContractViolation, ...] = ()
    evaluated_at: datetime = dataclass_field(
        default_factory=lambda: datetime.now(UTC)
    )

    @property
    def violation_count(self) -> int:
        return len(self.violations)
