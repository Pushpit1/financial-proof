"""Deterministic AI investigation engine."""

from app.application.ai_investigation.audit import (
    InvestigationAuditSink,
)
from app.application.ai_investigation.contracts import (
    InvestigationToolRequest,
    InvestigationToolResult,
)
from app.application.ai_investigation.registry import (
    InvestigationToolRegistry,
)


class AIInvestigationEngine:
    """Orchestrate bounded, deterministic investigation tool calls."""

    def __init__(
        self,
        registry: InvestigationToolRegistry,
        audit_sink: InvestigationAuditSink | None = None,
    ) -> None:
        self._registry = registry
        self._audit_sink = audit_sink

    def investigate(
        self,
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        """Execute exactly one authorized investigation tool and audit it."""
        result = self._registry.execute(request)

        if self._audit_sink is not None:
            from app.application.ai_investigation.audit import (
                InvestigationAuditRecord,
            )

            self._audit_sink.record(
                InvestigationAuditRecord.from_result(
                    request,
                    result,
                )
            )

        return result
