"""Immutable audit contracts for AI investigation."""

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.application.ai_investigation.contracts import (
    InvestigationToolRequest,
    InvestigationToolResult,
)


class InvestigationAuditRecord(BaseModel):
    """Immutable record of one investigation tool invocation."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    audit_id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    tool: str
    target_id: UUID

    request_arguments: dict[str, object] = Field(default_factory=dict)

    status: str
    result_data: dict[str, object] = Field(default_factory=dict)
    evidence_ids: tuple[UUID, ...] = ()
    explanation: str | None = None

    grounded: bool = True
    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    @classmethod
    def from_result(
        cls,
        request: InvestigationToolRequest,
        result: InvestigationToolResult,
    ) -> "InvestigationAuditRecord":
        """Create an audit record from a deterministic tool result."""
        return cls(
            investigation_id=request.investigation_id,
            tool=request.tool.value,
            target_id=request.target_id,
            request_arguments=dict(request.arguments),
            status=result.status.value,
            result_data=dict(result.data),
            evidence_ids=result.evidence_ids,
            explanation=result.explanation,
        )


class InvestigationAuditSink(Protocol):
    """Persistence boundary for investigation audit records."""

    def record(
        self,
        audit_record: InvestigationAuditRecord,
    ) -> None:
        """Record one immutable investigation event."""
        ...


class InMemoryInvestigationAuditSink:
    """Deterministic in-memory audit sink for application use and tests."""

    def __init__(self) -> None:
        self._records: list[InvestigationAuditRecord] = []

    def record(
        self,
        audit_record: InvestigationAuditRecord,
    ) -> None:
        """Append an immutable audit record."""
        self._records.append(audit_record)

    def records(self) -> tuple[InvestigationAuditRecord, ...]:
        """Return audit records in insertion order."""
        return tuple(self._records)
