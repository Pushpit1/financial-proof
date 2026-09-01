"""SQLAlchemy persistence model for financial guardian audit records."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FinancialGuardianAuditRecordModel(Base):
    """Persisted immutable financial guardian audit record."""

    __tablename__ = "financial_guardian_audit_records"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    operation: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    rule: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
