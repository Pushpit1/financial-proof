from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class VerificationResult(BaseModel):
    """Immutable deterministic result of before/after verification."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    verification_id: UUID = Field(default_factory=uuid4)

    before_snapshot_id: UUID
    after_snapshot_id: UUID
    comparison_id: UUID

    passed: bool
    regression_detected: bool

    violations: tuple[str, ...] = ()
    reproducible: bool = True
