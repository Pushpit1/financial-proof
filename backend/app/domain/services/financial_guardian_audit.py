from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.models.financial_guardian_audit import (
    FinancialGuardianAuditRecord,
)


class FinancialGuardianAuditService:
    """Create immutable audit records for Guardian decisions."""

    @staticmethod
    def record(
        evaluation: GuardianEvaluation,
        *,
        operation: str,
        actor_id: str | None = None,
    ) -> FinancialGuardianAuditRecord:
        """Convert a Guardian evaluation into an audit record."""

        if not operation.strip():
            raise ValueError("Operation cannot be empty.")

        if actor_id is not None and not actor_id.strip():
            raise ValueError("Actor ID cannot be empty.")

        return FinancialGuardianAuditRecord(
            actor_id=actor_id,
            operation=operation,
            rule=evaluation.rule,
            decision=evaluation.decision,
            reason=evaluation.reason,
        )
