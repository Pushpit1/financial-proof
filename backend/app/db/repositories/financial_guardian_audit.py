"""SQLAlchemy repository for financial guardian audit records."""

from app.application.ports.financial_guardian_audit import (
    FinancialGuardianAuditRepository,
)
from app.db.mappers.financial import (
    financial_guardian_audit_to_domain,
    financial_guardian_audit_to_model,
)
from app.domain.models.financial_guardian_audit import (
    FinancialGuardianAuditRecord,
)


class SqlAlchemyFinancialGuardianAuditRepository(
    FinancialGuardianAuditRepository,
):
    """SQLAlchemy implementation of guardian audit persistence."""

    def __init__(self, session) -> None:
        self.session = session

    def save(
        self,
        record: FinancialGuardianAuditRecord,
    ) -> FinancialGuardianAuditRecord:
        """Persist and return the immutable domain record."""
        model = financial_guardian_audit_to_model(record)
        self.session.add(model)
        self.session.flush()
        return financial_guardian_audit_to_domain(model)

