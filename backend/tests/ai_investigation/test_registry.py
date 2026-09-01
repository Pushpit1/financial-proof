from uuid import uuid4

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    ToolExecutionStatus,
)
from app.application.ai_investigation.registry import (
    InvestigationToolRegistry,
    build_investigation_tool_registry,
)
from app.domain.models.financial import FinancialContract


def test_registry_registers_and_executes_handler() -> None:
    registry = InvestigationToolRegistry()

    def handler(request):
        from app.application.ai_investigation.contracts import (
            InvestigationToolResult,
        )

        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"source": "deterministic-test-handler"},
        )

    registry.register(
        InvestigationTool.INSPECT_CONTRACT,
        handler,
    )

    request = InvestigationToolRequest(
        tool=InvestigationTool.INSPECT_CONTRACT,
        target_id=uuid4(),
    )

    result = registry.execute(request)

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.data == {"source": "deterministic-test-handler"}
    assert result.investigation_id == request.investigation_id


def test_registry_reports_missing_handler() -> None:
    registry = InvestigationToolRegistry()

    request = InvestigationToolRequest(
        tool=InvestigationTool.INSPECT_STATE,
        target_id=uuid4(),
    )

    result = registry.execute(request)

    assert result.status is ToolExecutionStatus.NOT_FOUND
    assert result.tool is InvestigationTool.INSPECT_STATE


def test_registry_contains_registered_tool() -> None:
    registry = InvestigationToolRegistry()

    registry.register(
        InvestigationTool.INSPECT_EXECUTION,
        lambda request: None,
    )

    assert registry.contains(InvestigationTool.INSPECT_EXECUTION)
    assert not registry.contains(InvestigationTool.INSPECT_STATE)


def test_registry_returns_tools_in_enum_order() -> None:
    registry = InvestigationToolRegistry()

    registry.register(
        InvestigationTool.REPLAY_SCENARIO,
        lambda request: None,
    )
    registry.register(
        InvestigationTool.INSPECT_CONTRACT,
        lambda request: None,
    )

    assert registry.tools() == (
        InvestigationTool.INSPECT_CONTRACT,
        InvestigationTool.REPLAY_SCENARIO,
    )


def test_registry_can_replace_handler() -> None:
    registry = InvestigationToolRegistry()

    registry.register(
        InvestigationTool.INSPECT_CONTRACT,
        lambda request: None,
    )

    def replacement(request):
        from app.application.ai_investigation.contracts import (
            InvestigationToolResult,
        )

        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"source": "replacement"},
        )

    registry.register(
        InvestigationTool.INSPECT_CONTRACT,
        replacement,
    )

    request = InvestigationToolRequest(
        tool=InvestigationTool.INSPECT_CONTRACT,
        target_id=uuid4(),
    )

    result = registry.execute(request)

    assert result.data == {"source": "replacement"}


def test_default_registry_wires_inspect_contract() -> None:
    contract = FinancialContract(
        name="Registry Contract",
        version=4,
    )

    registry = build_investigation_tool_registry(
        {str(contract.id): contract},
    )

    assert registry.contains(InvestigationTool.INSPECT_CONTRACT)
    assert registry.tools() == (
        InvestigationTool.INSPECT_CONTRACT,
    )

    result = registry.execute(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=contract.id,
        )
    )

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.data["id"] == str(contract.id)
    assert result.data["name"] == "Registry Contract"
    assert result.data["version"] == 4
    
def test_registry_denies_execution_without_permission() -> None:
    registry = InvestigationToolRegistry(
        permissions=set(),
    )

    def handler(request):
        from app.application.ai_investigation.contracts import (
            InvestigationToolResult,
        )

        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"executed": True},
        )

    registry.register(
        InvestigationTool.INSPECT_CONTRACT,
        handler,
    )

    request = InvestigationToolRequest(
        tool=InvestigationTool.INSPECT_CONTRACT,
        target_id=uuid4(),
    )

    result = registry.execute(request)

    assert result.status is ToolExecutionStatus.FORBIDDEN
    assert result.data == {}


def test_registry_can_grant_and_revoke_permission() -> None:
    registry = InvestigationToolRegistry(
        permissions=set(),
    )

    registry.register(
        InvestigationTool.INSPECT_CONTRACT,
        lambda request: None,
    )

    assert not registry.is_permitted(
        InvestigationTool.INSPECT_CONTRACT,
    )

    registry.grant(InvestigationTool.INSPECT_CONTRACT)

    assert registry.is_permitted(
        InvestigationTool.INSPECT_CONTRACT,
    )

    registry.revoke(InvestigationTool.INSPECT_CONTRACT)

    assert not registry.is_permitted(
        InvestigationTool.INSPECT_CONTRACT,
    )


def test_default_registry_explicitly_permits_inspect_contract() -> None:
    contract = FinancialContract(
        name="Permission Contract",
        version=1,
    )

    registry = build_investigation_tool_registry(
        {str(contract.id): contract},
    )

    assert registry.is_permitted(
        InvestigationTool.INSPECT_CONTRACT,
    )
    assert registry.permitted_tools() == (
        InvestigationTool.INSPECT_CONTRACT,
    )

