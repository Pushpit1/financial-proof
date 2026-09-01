"""Tests for deterministic investigation tool contracts."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)


def test_investigation_tool_contains_required_tools() -> None:
    assert {
        tool.value
        for tool in InvestigationTool
    } == {
        "inspect_contract",
        "inspect_execution",
        "inspect_state",
        "inspect_violation",
        "inspect_financial_impact",
        "replay_scenario",
        "compare_expected_actual",
    }


def test_tool_request_has_stable_investigation_id() -> None:
    target_id = uuid4()

    request = InvestigationToolRequest(
        tool=InvestigationTool.INSPECT_CONTRACT,
        target_id=target_id,
    )

    assert request.investigation_id is not None
    assert request.target_id == target_id
    assert request.arguments == {}


def test_tool_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=uuid4(),
            unexpected="value",
        )


def test_tool_result_preserves_deterministic_payload() -> None:
    investigation_id = uuid4()
    target_id = uuid4()

    result = InvestigationToolResult(
        investigation_id=investigation_id,
        tool=InvestigationTool.INSPECT_FINANCIAL_IMPACT,
        target_id=target_id,
        status=ToolExecutionStatus.SUCCESS,
        data={
            "actual_exposure": "100.00",
            "maximum_exposure": "200.00",
        },
        explanation="Financial impact was calculated by the deterministic blast-radius service.",
    )

    assert result.is_success
    assert result.data["actual_exposure"] == "100.00"
    assert result.data["maximum_exposure"] == "200.00"


def test_failed_tool_result_is_not_success() -> None:
    result = InvestigationToolResult(
        investigation_id=uuid4(),
        tool=InvestigationTool.INSPECT_VIOLATION,
        target_id=uuid4(),
        status=ToolExecutionStatus.NOT_FOUND,
    )

    assert not result.is_success



def test_investigation_result_defaults_data_to_empty_dict() -> None:
    result = InvestigationToolResult(
        investigation_id=uuid4(),
        tool=InvestigationTool.INSPECT_STATE,
        target_id=uuid4(),
        status=ToolExecutionStatus.NOT_FOUND,
    )

    assert result.data == {}


def test_investigation_result_is_success_only_for_success_status() -> None:
    result = InvestigationToolResult(
        investigation_id=uuid4(),
        tool=InvestigationTool.INSPECT_STATE,
        target_id=uuid4(),
        status=ToolExecutionStatus.FORBIDDEN,
    )

    assert result.is_success is False
