import json
from uuid import uuid4

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)
from app.application.ai_investigation.engine import AIInvestigationEngine
from app.application.ai_investigation.registry import InvestigationToolRegistry
from app.core.logging import configure_logging


def read_json_events(output: str) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in output.splitlines()
        if line.strip()
    ]


def test_engine_logs_investigation_lifecycle(capsys) -> None:
    configure_logging()

    investigation_id = uuid4()
    target_id = uuid4()

    def handler(
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            evidence_ids=(uuid4(), uuid4()),
            data={"result": "deterministic"},
        )

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_STATE: handler,
        },
    )

    registry.grant(InvestigationTool.INSPECT_STATE)

    result = AIInvestigationEngine(registry).investigate(
        InvestigationToolRequest(
            investigation_id=investigation_id,
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    events = read_json_events(capsys.readouterr().out)

    started = [
        event
        for event in events
        if event.get("event") == "ai_investigation_started"
    ]

    completed = [
        event
        for event in events
        if event.get("event") == "ai_investigation_completed"
    ]

    assert started
    assert completed

    start_event = started[-1]
    complete_event = completed[-1]

    assert start_event["investigation_id"] == str(investigation_id)
    assert start_event["tool"] == "inspect_state"
    assert start_event["target_id"] == str(target_id)

    assert complete_event["investigation_id"] == str(investigation_id)
    assert complete_event["tool"] == "inspect_state"
    assert complete_event["target_id"] == str(target_id)
    assert complete_event["status"] == "success"
    assert complete_event["evidence_count"] == 2

    assert result.status is ToolExecutionStatus.SUCCESS


def test_engine_logs_forbidden_investigation_result(capsys) -> None:
    configure_logging()

    investigation_id = uuid4()
    target_id = uuid4()

    registry = InvestigationToolRegistry(
        permissions=set(),
    )

    registry.register(
        InvestigationTool.INSPECT_STATE,
        lambda request: InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"unexpected": True},
        ),
    )

    result = AIInvestigationEngine(registry).investigate(
        InvestigationToolRequest(
            investigation_id=investigation_id,
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    events = read_json_events(capsys.readouterr().out)

    completed = [
        event
        for event in events
        if event.get("event") == "ai_investigation_completed"
    ]

    assert completed

    event = completed[-1]

    assert event["investigation_id"] == str(investigation_id)
    assert event["status"] == "forbidden"
    assert event["evidence_count"] == 0
    assert result.status is ToolExecutionStatus.FORBIDDEN


def test_engine_preserves_investigation_result_exactly() -> None:
    investigation_id = uuid4()
    target_id = uuid4()
    evidence_ids = (uuid4(),)

    expected = InvestigationToolResult(
        investigation_id=investigation_id,
        tool=InvestigationTool.INSPECT_STATE,
        target_id=target_id,
        status=ToolExecutionStatus.SUCCESS,
        evidence_ids=evidence_ids,
        data={"value": "preserved"},
        explanation="Deterministic result.",
    )

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_STATE: lambda request: expected,
        },
    )

    registry.grant(InvestigationTool.INSPECT_STATE)

    actual = AIInvestigationEngine(registry).investigate(
        InvestigationToolRequest(
            investigation_id=investigation_id,
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    assert actual is expected
