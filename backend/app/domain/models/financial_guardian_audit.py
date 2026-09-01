from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums.financial_guardian import GuardianDecision


class FinancialGuardianAuditRecord(BaseModel):
    """Immutable record of a runtime financial-guardian decision."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: UUID = Field(default_factory=uuid4)
    actor_id: str | None = None
    operation: str
    rule: str
    decision: GuardianDecision
    reason: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
