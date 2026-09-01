from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class VerificationChange(BaseModel):
    """Immutable deterministic description of one verification change."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    field: str
    before: Any = None
    after: Any = None
    change_type: str


class VerificationComparison(BaseModel):
    """Deterministic immutable comparison between two verification snapshots."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    before_snapshot_id: UUID
    after_snapshot_id: UUID

    contract_version_changed: bool
    system_version_changed: bool

    changes: tuple[VerificationChange, ...] = ()

    added_changes: tuple[str, ...] = ()
    removed_changes: tuple[str, ...] = ()

    introduced_violations: tuple[str, ...] = ()
    resolved_violations: tuple[str, ...] = ()

    added_counterexample_ids: tuple[UUID, ...] = ()
    removed_counterexample_ids: tuple[UUID, ...] = ()

    regression_detected: bool = False

    comparison_id: UUID = Field(default_factory=uuid4)
