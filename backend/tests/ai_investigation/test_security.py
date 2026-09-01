"""Security tests for AI investigation tools."""

from uuid import uuid4

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)
from app.application.ai_investigation.registry import InvestigationToolRegistry
from app.application.ai_investigation.security import (
    InvestigationToolSecurityPolicy,
)


def test_security_policy_allows_declared_contract_argument() -> None:
    policy = InvestigationToolSecurityPolicy()

    policy.validate(
        InvestigationTool.INSPECT_CONTRACT,
        {"include_constraints": True},
    )


def test_security_policy_rejects_unknown_argument() -> None:
    policy = InvestigationToolSecurityPolicy()

    try:
        policy.validate(
            InvestigationTool.INSPECT_CONTRACT,
            {"execute": True},
        )
    except ValueError as exc:
        assert "not allowed" in str(exc)
    else:
        raise AssertionError("Unknown tool argument must be rejected.")


def test_security_policy_rejects_arguments_for_tools_without_arguments() -> None:
    policy = InvestigationToolSecurityPolicy()

    try:
        policy.validate(
            InvestigationTool.INSPECT_STATE,
            {"field": "state"},
        )
    except ValueError as exc:
        assert "not allowed" in str(exc)
    else:
        raise AssertionError("Undeclared arguments must be rejected.")


def test_security_policy_rejects_oversized_string() -> None:
    policy = InvestigationToolSecurityPolicy()

    try:
        policy.validate(
            InvestigationTool.INSPECT_CONTRACT,
            {"include_constraints": "x" * 513},
        )
    except ValueError as exc:
        assert "string exceeds" in str(exc)
    else:
        raise AssertionError("Oversized strings must be rejected.")


def test_security_policy_rejects_deep_nesting() -> None:
    policy = InvestigationToolSecurityPolicy()

    nested = {"a": {"b": {"c": {"d": True}}}}

    try:
        policy.validate(
            InvestigationTool.INSPECT_CONTRACT,
            {"include_constraints": nested},
        )
    except ValueError as exc:
        assert "nesting exceeds" in str(exc)
    else:
        raise AssertionError("Deeply nested arguments must be rejected.")


def test_registry_denies_invalid_arguments_before_handler_execution() -> None:
    executed = False

    def handler(
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        nonlocal executed
        executed = True

        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"executed": True},
        )

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_CONTRACT: handler,
        },
        permissions={
            InvestigationTool.INSPECT_CONTRACT,
        },
    )

    result = registry.execute(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=uuid4(),
            arguments={"execute": True},
        )
    )

    assert result.status is ToolExecutionStatus.DENIED
    assert result.data == {}
    assert executed is False


def test_registry_contains_tool_failure_without_leaking_exception() -> None:
    def handler(
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        raise RuntimeError("secret internal failure")

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_CONTRACT: handler,
        },
        permissions={
            InvestigationTool.INSPECT_CONTRACT,
        },
    )

    result = registry.execute(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=uuid4(),
        )
    )

    assert result.status is ToolExecutionStatus.FAILED
    assert result.data == {}
    assert "secret internal failure" not in (result.explanation or "")


def test_registry_rejects_handler_result_identity_mismatch() -> None:
    target_id = uuid4()

    def handler(
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        return InvestigationToolResult(
            investigation_id=uuid4(),
            tool=request.tool,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data={"unexpected": True},
        )

    registry = InvestigationToolRegistry(
        handlers={
            InvestigationTool.INSPECT_CONTRACT: handler,
        },
        permissions={
            InvestigationTool.INSPECT_CONTRACT,
        },
    )

    result = registry.execute(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=target_id,
        )
    )

    assert result.status is ToolExecutionStatus.FAILED
    assert result.data == {}
    assert "invalid result identity" in (result.explanation or "")
