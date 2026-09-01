"""Persistence port for financial guardian audit records."""

from abc import ABC, abstractmethod

from app.domain.models.financial_guardian_audit import (
    FinancialGuardianAuditRecord,
)


class FinancialGuardianAuditRepository(ABC):
    """Persistence contract for immutable guardian audit records."""

    @abstractmethod
    def save(
        self,
        record: FinancialGuardianAuditRecord,
    ) -> FinancialGuardianAuditRecord:
        """Persist an audit record."""

        raise NotImplementedError
