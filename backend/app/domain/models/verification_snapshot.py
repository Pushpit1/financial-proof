from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class VerificationSnapshot(BaseModel):
    """Immutable snapshot of the system state used for verification."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    snapshot_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    contract_id: UUID | None = None
    contract_version: str
    system_version: str

    baseline: dict[str, Any] = Field(default_factory=dict)
    violations: tuple[str, ...] = ()
    counterexample_ids: tuple[UUID, ...] = ()

    simulation_id: UUID | None = None

    reproducibility_metadata: dict[str, Any] = Field(
        default_factory=dict,
    )
