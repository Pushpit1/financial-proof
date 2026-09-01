import structlog

from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.financial_guardian_audit import FinancialGuardianAuditRecord

logger = structlog.get_logger(__name__)


class FinancialGuardianAuditService:
    """Create immutable audit records for Guardian decisions."""

    @staticmethod
    def record(
        evaluation: GuardianEvaluation,
        *,
        operation: str,
        actor_id: str | None = None,
    ) -> FinancialGuardianAuditRecord:
        if not operation.strip():
            raise ValueError("Operation cannot be empty.")

        if actor_id is not None and not actor_id.strip():
            raise ValueError("Actor ID cannot be empty.")

        record = FinancialGuardianAuditRecord(
            actor_id=actor_id,
            operation=operation,
            rule=evaluation.rule,
            decision=evaluation.decision,
            reason=evaluation.reason,
        )

        fields: dict[str, object] = {
            "audit_id": str(record.id),
            "operation": record.operation,
            "rule": record.rule,
            "decision": record.decision.value,
            "reason": record.reason,
        }

        if record.actor_id is not None:
            fields["actor_id"] = record.actor_id

        logger.info(
            "guardian_audit_recorded",
            **fields,
        )

        return record
