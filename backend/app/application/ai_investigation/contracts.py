"""Contracts for deterministic investigation tools."""

from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class InvestigationTool(StrEnum):
    """Tools available to the investigation engine."""

    INSPECT_CONTRACT = "inspect_contract"
    INSPECT_EXECUTION = "inspect_execution"
    INSPECT_STATE = "inspect_state"
    INSPECT_VIOLATION = "inspect_violation"
    INSPECT_FINANCIAL_IMPACT = "inspect_financial_impact"
    REPLAY_SCENARIO = "replay_scenario"
    COMPARE_EXPECTED_ACTUAL = "compare_expected_actual"


class ToolExecutionStatus(StrEnum):
    """Outcome of a deterministic tool invocation."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"
    DENIED = "denied"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class InvestigationToolRequest(BaseModel):
    """Validated request issued to one investigation tool."""

    model_config = ConfigDict(extra="forbid")

    investigation_id: UUID = Field(default_factory=uuid4)
    tool: InvestigationTool
    target_id: UUID
    arguments: dict[str, Any] = Field(default_factory=dict)


class InvestigationToolResult(BaseModel):
    """Deterministic result returned by an investigation tool."""

    model_config = ConfigDict(extra="forbid")

    investigation_id: UUID
    tool: InvestigationTool
    target_id: UUID
    status: ToolExecutionStatus
    data: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: tuple[UUID, ...] = ()
    explanation: str | None = None

    @property
    def is_success(self) -> bool:
        """Return whether the tool completed successfully."""
        return self.status is ToolExecutionStatus.SUCCESS
