"""API schemas for deterministic verification."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VerificationSnapshotRequest(BaseModel):
    """Snapshot evidence supplied to the verification API."""

    model_config = ConfigDict(extra="forbid")

    contract_id: UUID | None = None
    contract_version: str = Field(min_length=1)
    system_version: str = Field(min_length=1)
    baseline: dict[str, Any] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)
    counterexample_ids: list[UUID] = Field(default_factory=list)
    simulation_id: UUID | None = None
    reproducibility_metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class VerificationRequest(BaseModel):
    """Request for before/after deterministic verification."""

    model_config = ConfigDict(extra="forbid")

    before: VerificationSnapshotRequest
    after: VerificationSnapshotRequest


class VerificationChangeResponse(BaseModel):
    """One deterministic change discovered between snapshots."""

    model_config = ConfigDict(extra="forbid")

    field: str
    before: Any = None
    after: Any = None
    change_type: str


class VerificationSnapshotResponse(BaseModel):
    """Immutable verification snapshot returned by the API."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: UUID
    created_at: str
    contract_id: UUID | None
    contract_version: str
    system_version: str
    baseline: dict[str, Any]
    violations: list[str]
    counterexample_ids: list[UUID]
    simulation_id: UUID | None
    reproducibility_metadata: dict[str, Any]


class VerificationComparisonResponse(BaseModel):
    """Before/after comparison returned by the verification API."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: UUID
    before_snapshot_id: UUID
    after_snapshot_id: UUID
    contract_version_changed: bool
    system_version_changed: bool
    changes: list[VerificationChangeResponse]
    added_changes: list[str]
    removed_changes: list[str]
    introduced_violations: list[str]
    resolved_violations: list[str]
    added_counterexample_ids: list[UUID]
    removed_counterexample_ids: list[UUID]
    regression_detected: bool


class VerificationResultResponse(BaseModel):
    """Final deterministic verification result."""

    model_config = ConfigDict(extra="forbid")

    verification_id: UUID
    before_snapshot_id: UUID
    after_snapshot_id: UUID
    comparison_id: UUID
    passed: bool
    regression_detected: bool
    violations: list[str]
    reproducible: bool


class VerificationResponse(BaseModel):
    """Complete verification response."""

    model_config = ConfigDict(extra="forbid")

    result: VerificationResultResponse
    before: VerificationSnapshotResponse
    after: VerificationSnapshotResponse
    comparison: VerificationComparisonResponse
