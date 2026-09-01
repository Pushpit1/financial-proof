"""Application orchestration for runtime financial guardian decisions."""

from collections.abc import Sequence

from app.application.ports.financial_guardian_audit import (
    FinancialGuardianAuditRepository,
)
from app.domain.models.financial_guardian import GuardianEvaluation
from app.domain.services.financial_guardian_audit import (
    FinancialGuardianAuditService,
)
from app.domain.services.guardian_policy import GuardianPolicy


class FinancialGuardianRuntime:
    """Coordinate deterministic Guardian evaluations and auditing."""

    def __init__(
        self,
        audit_repository: FinancialGuardianAuditRepository | None = None,
    ) -> None:
        self._policy = GuardianPolicy()
        self._audit_repository = audit_repository

    def decide(
        self,
        evaluations: Sequence[GuardianEvaluation],
        *,
        operation: str | None = None,
        actor_id: str | None = None,
    ) -> GuardianEvaluation:
        """Return the final deterministic Guardian decision."""
        evaluation = self._policy.decide(evaluations)

        if self._audit_repository is not None:
            if operation is None:
                raise ValueError(
                    "Operation is required when audit persistence is enabled.",
                )

            record = FinancialGuardianAuditService.record(
                evaluation,
                operation=operation,
                actor_id=actor_id,
            )
            self._audit_repository.save(record)

        return evaluation
