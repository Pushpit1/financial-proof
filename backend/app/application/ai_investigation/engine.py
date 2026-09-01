"""Deterministic AI investigation engine."""

from app.application.ai_investigation.audit import (
    InvestigationAuditRecord,
    InvestigationAuditSink,
)
from app.application.ai_investigation.contracts import (
    InvestigationToolRequest,
    InvestigationToolResult,
)
from app.application.ai_investigation.registry import (
    InvestigationToolRegistry,
)
from app.core.logging import get_logger, log_event
from app.core.metrics import get_metrics_registry

logger = get_logger(__name__)


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
        """Execute exactly one authorized investigation tool."""

        log_event(
            logger,
            "ai_investigation_started",
            fields={
                "investigation_id": str(request.investigation_id),
                "tool": request.tool.value,
                "target_id": str(request.target_id),
            },
        )

        result = self._registry.execute(request)

        metrics = get_metrics_registry()
        metrics.counter("ai_investigations_total").increment()
        metrics.counter(
            f"ai_investigation_{result.status.value}_total",
        ).increment()

        if self._audit_sink is not None:
            audit_record = InvestigationAuditRecord.from_result(
                request,
                result,
            )
            self._audit_sink.record(audit_record)

            log_event(
                logger,
                "ai_investigation_audited",
                fields={
                    "audit_id": str(audit_record.audit_id),
                    "investigation_id": str(audit_record.investigation_id),
                    "tool": audit_record.tool,
                    "target_id": str(audit_record.target_id),
                    "status": audit_record.status,
                    "evidence_count": len(audit_record.evidence_ids),
                },
            )

        log_event(
            logger,
            "ai_investigation_completed",
            fields={
                "investigation_id": str(result.investigation_id),
                "tool": result.tool.value,
                "target_id": str(result.target_id),
                "status": result.status.value,
                "evidence_count": len(result.evidence_ids),
            },
        )

        return result
