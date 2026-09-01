from uuid import uuid4

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)
from app.application.ai_investigation.engine import AIInvestigationEngine
from app.application.ai_investigation.registry import (
    InvestigationToolRegistry,
)


def test_engine_delegates_to_registered_tool() -> None:
    target_id = uuid4()

    def handler(
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"bounded": True},
        )

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_STATE: handler,
        },
    )

    result = AIInvestigationEngine(registry).investigate(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.target_id == target_id
    assert result.data == {"bounded": True}


def test_engine_preserves_forbidden_result() -> None:
    target_id = uuid4()

    def handler(
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        raise AssertionError("forbidden tools must never execute")

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_STATE: handler,
        },
        permissions=set(),
    )

    result = AIInvestigationEngine(registry).investigate(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    assert result.status is ToolExecutionStatus.FORBIDDEN
    assert result.data == {}


def test_engine_returns_not_found_for_unregistered_tool() -> None:
    target_id = uuid4()

    registry = InvestigationToolRegistry()

    result = AIInvestigationEngine(registry).investigate(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    assert result.status is ToolExecutionStatus.NOT_FOUND
    assert result.data == {}


def test_engine_does_not_generate_investigation_claims() -> None:
    target_id = uuid4()

    def handler(
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"state": "known"},
        )

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_STATE: handler,
        },
    )

    result = AIInvestigationEngine(registry).investigate(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_STATE,
            target_id=target_id,
        ),
    )

    assert result.data == {"state": "known"}
    assert "root_cause" not in result.data
    assert "recommendation" not in result.data
