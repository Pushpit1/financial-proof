"""Deterministic investigation tool registry."""

from collections.abc import Callable
from dataclasses import dataclass

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)
from app.application.ai_investigation.security import (
    InvestigationToolSecurityError,
    InvestigationToolSecurityPolicy,
)
from app.domain.models.financial import FinancialContract

ToolHandler = Callable[[InvestigationToolRequest], InvestigationToolResult]


@dataclass(frozen=True)
class InvestigationPermission:
    """Permission granted to execute one investigation tool."""

    tool: InvestigationTool
    allowed: bool = True


class InvestigationToolRegistry:
    """Registry that maps investigation tools to deterministic handlers."""

    def __init__(
        self,
        handlers: dict[InvestigationTool, ToolHandler] | None = None,
        permissions: set[InvestigationTool] | None = None,
        security_policy: InvestigationToolSecurityPolicy | None = None,
    ) -> None:
        self._handlers = dict(handlers or {})
        self._permissions = (
            None
            if permissions is None
            else set(permissions)
        )
        self._security_policy = (
            security_policy or InvestigationToolSecurityPolicy()
        )

    def register(
        self,
        tool: InvestigationTool,
        handler: ToolHandler,
    ) -> None:
        """Register or replace a deterministic tool handler."""
        self._handlers[tool] = handler

    def grant(self, tool: InvestigationTool) -> None:
        """Grant permission to execute a registered tool."""
        if self._permissions is None:
            self._permissions = set(self._handlers)

        self._permissions.add(tool)

    def revoke(self, tool: InvestigationTool) -> None:
        """Revoke permission to execute a tool."""
        if self._permissions is None:
            self._permissions = set(self._handlers)

        self._permissions.discard(tool)

    def contains(self, tool: InvestigationTool) -> bool:
        """Return whether a tool has a registered handler."""
        return tool in self._handlers

    def is_permitted(self, tool: InvestigationTool) -> bool:
        """Return whether a tool is currently permitted."""
        if self._permissions is None:
            return tool in self._handlers

        return tool in self._permissions

    def tools(self) -> tuple[InvestigationTool, ...]:
        """Return registered tools in deterministic enum order."""
        return tuple(
            tool
            for tool in InvestigationTool
            if tool in self._handlers
        )

    def permitted_tools(self) -> tuple[InvestigationTool, ...]:
        """Return permitted registered tools in deterministic order."""
        return tuple(
            tool
            for tool in self.tools()
            if self.is_permitted(tool)
        )

    def execute(
        self,
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        """Execute a registered and security-approved deterministic tool."""

        handler = self._handlers.get(request.tool)

        if handler is None:
            return InvestigationToolResult(
                investigation_id=request.investigation_id,
                tool=request.tool,
                target_id=request.target_id,
                status=ToolExecutionStatus.NOT_FOUND,
                data={},
                explanation=(
                    f"No handler registered for tool "
                    f"'{request.tool.value}'."
                ),
            )

        if not self.is_permitted(request.tool):
            return InvestigationToolResult(
                investigation_id=request.investigation_id,
                tool=request.tool,
                target_id=request.target_id,
                status=ToolExecutionStatus.FORBIDDEN,
                data={},
                explanation=(
                    f"Permission denied for tool "
                    f"'{request.tool.value}'."
                ),
            )

        try:
            self._security_policy.validate(
                request.tool,
                request.arguments,
            )
        except InvestigationToolSecurityError as exc:
            return InvestigationToolResult(
                investigation_id=request.investigation_id,
                tool=request.tool,
                target_id=request.target_id,
                status=ToolExecutionStatus.DENIED,
                data={},
                explanation=str(exc),
            )

        try:
            result = handler(request)
        except Exception:
            return InvestigationToolResult(
                investigation_id=request.investigation_id,
                tool=request.tool,
                target_id=request.target_id,
                status=ToolExecutionStatus.FAILED,
                data={},
                explanation="Investigation tool execution failed.",
            )

        if (
            result.investigation_id != request.investigation_id
            or result.tool is not request.tool
            or result.target_id != request.target_id
        ):
            return InvestigationToolResult(
                investigation_id=request.investigation_id,
                tool=request.tool,
                target_id=request.target_id,
                status=ToolExecutionStatus.FAILED,
                data={},
                explanation="Investigation tool returned an invalid result identity.",
            )

        return result


def build_investigation_tool_registry(
    contracts: dict[str, object],
) -> InvestigationToolRegistry:
    """Build the default deterministic investigation tool registry."""
    from app.application.ai_investigation.inspect_contract import (
        InspectContractTool,
    )

    typed_contracts = {
        key: value
        for key, value in contracts.items()
        if isinstance(value, FinancialContract)
    }

    registry = InvestigationToolRegistry(
        permissions=set(),
    )

    registry.register(
        InvestigationTool.INSPECT_CONTRACT,
        InspectContractTool(typed_contracts),
    )

    registry.grant(InvestigationTool.INSPECT_CONTRACT)

    return registry
