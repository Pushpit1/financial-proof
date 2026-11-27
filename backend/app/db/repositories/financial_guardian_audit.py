"""SQLAlchemy repository for financial guardian audit records."""

from sqlalchemy import select

from app.application.ports.financial_guardian_audit import (
    FinancialGuardianAuditRepository,
)
from app.db.mappers.financial import (
    financial_guardian_audit_to_domain,
    financial_guardian_audit_to_model,
)
from app.db.models.financial_guardian_audit import (
    FinancialGuardianAuditRecordModel,
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

    def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FinancialGuardianAuditRecord]:
        """List persisted guardian audit records ordered newest first."""
        statement = (
            select(FinancialGuardianAuditRecordModel)
            .order_by(FinancialGuardianAuditRecordModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [
            financial_guardian_audit_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]
