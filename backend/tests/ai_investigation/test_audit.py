from uuid import uuid4

import pytest

from app.application.ai_investigation.audit import (
    InMemoryInvestigationAuditSink,
    InvestigationAuditRecord,
)
from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)
from app.application.ai_investigation.engine import AIInvestigationEngine
from app.application.ai_investigation.registry import InvestigationToolRegistry


def test_audit_record_is_created_from_tool_result() -> None:
    investigation_id = uuid4()
    target_id = uuid4()
    evidence_id = uuid4()

    request = InvestigationToolRequest(
        investigation_id=investigation_id,
        tool=InvestigationTool.INSPECT_CONTRACT,
        target_id=target_id,
        arguments={"include_constraints": True},
    )

    result = InvestigationToolResult(
        investigation_id=investigation_id,
        tool=InvestigationTool.INSPECT_CONTRACT,
        target_id=target_id,
        status=ToolExecutionStatus.SUCCESS,
        data={"contract_id": str(target_id)},
        evidence_ids=(evidence_id,),
        explanation="Contract inspected successfully.",
    )

    record = InvestigationAuditRecord.from_result(
        request,
        result,
    )

    assert record.investigation_id == investigation_id
    assert record.tool == "inspect_contract"
    assert record.target_id == target_id
    assert record.request_arguments == {
        "include_constraints": True,
    }
    assert record.result_data == {
        "contract_id": str(target_id),
    }
    assert record.evidence_ids == (evidence_id,)
    assert record.grounded is True


def test_audit_record_is_immutable() -> None:
    record = InvestigationAuditRecord(
        investigation_id=uuid4(),
        tool="inspect_contract",
        target_id=uuid4(),
        status="success",
    )

    from pydantic import ValidationError

    with pytest.raises(
        ValidationError,
        match="Instance is frozen",
    ):
        record.tool = "inspect_state"


def test_engine_records_successful_investigation() -> None:
    target_id = uuid4()
    sink = InMemoryInvestigationAuditSink()

    def handler(request: InvestigationToolRequest) -> InvestigationToolResult:
        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"observed": "value"},
        )

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_STATE: handler,
        },
        permissions={
            InvestigationTool.INSPECT_STATE,
        },
    )

    result = AIInvestigationEngine(
        registry,
        audit_sink=sink,
    ).investigate(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    records = sink.records()

    assert result.status is ToolExecutionStatus.SUCCESS
    assert len(records) == 1
    assert records[0].status == "success"
    assert records[0].tool == "inspect_state"
    assert records[0].result_data == {
        "observed": "value",
    }


def test_engine_audits_forbidden_investigation() -> None:
    target_id = uuid4()
    sink = InMemoryInvestigationAuditSink()

    def handler(request: InvestigationToolRequest) -> InvestigationToolResult:
        raise AssertionError("Forbidden tools must never execute.")

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_STATE: handler,
        },
        permissions=set(),
    )

    result = AIInvestigationEngine(
        registry,
        audit_sink=sink,
    ).investigate(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    records = sink.records()

    assert result.status is ToolExecutionStatus.FORBIDDEN
    assert len(records) == 1
    assert records[0].status == "forbidden"
    assert records[0].result_data == {}
    assert records[0].grounded is True


def test_engine_audits_not_found_investigation() -> None:
    target_id = uuid4()
    sink = InMemoryInvestigationAuditSink()

    registry = InvestigationToolRegistry(
        handlers={},
        permissions=set(),
    )

    result = AIInvestigationEngine(
        registry,
        audit_sink=sink,
    ).investigate(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    records = sink.records()

    assert result.status is ToolExecutionStatus.NOT_FOUND
    assert len(records) == 1
    assert records[0].status == "not_found"
    assert records[0].grounded is True

