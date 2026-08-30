"""SQLAlchemy persistence models for financial domain objects."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UUIDModel(Base):
    """Base persistence model with eagerly generated defaults."""

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=lambda: uuid4(),
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("id", uuid4())
        super().__init__(**kwargs)


class EvidenceModel(UUIDModel):
    """Persistence model for financial evidence."""

    __tablename__ = "evidence"

    evidence_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    received_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    proof_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("financial_proofs.id"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="received",
    )

    checksum: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_reference: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("status", "received")
        super().__init__(**kwargs)


class FinancialClaimModel(UUIDModel):
    """Persistence model for normalized financial claims."""

    __tablename__ = "financial_claims"

    proof_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("financial_proofs.id"),
        nullable=True,
    )

    claim_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    period_start: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    period_end: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    amount: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unverified",
    )

    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )

    confidence_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="very_low",
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("verification_status", "unverified")
        kwargs.setdefault("confidence", Decimal("0"))
        kwargs.setdefault("confidence_level", "very_low")
        super().__init__(**kwargs)


class EvidenceLinkModel(UUIDModel):
    """Persistence model linking claims to evidence."""

    __tablename__ = "evidence_links"

    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("financial_claims.id"),
        nullable=False,
    )

    evidence_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence.id"),
        nullable=False,
    )

    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unverified",
    )

    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("verification_status", "unverified")
        kwargs.setdefault("confidence", Decimal("0"))
        super().__init__(**kwargs)


class FinancialContractModel(UUIDModel):
    """Persistence model for immutable financial proof contracts."""

    __tablename__ = "financial_contracts"

    __table_args__ = (
        UniqueConstraint(
            "name",
            "version",
            name="uq_financial_contract_name_version",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
    )

    minimum_confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )

    minimum_supported_claim_ratio: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("1"),
    )

    required_claim_types: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("version", 1)
        kwargs.setdefault("minimum_confidence", Decimal("0"))
        kwargs.setdefault("minimum_supported_claim_ratio", Decimal("1"))
        kwargs.setdefault("required_claim_types", [])
        super().__init__(**kwargs)


class FinancialProofModel(UUIDModel):
    """Persistence model for a defensible financial proof."""

    __tablename__ = "financial_proofs"

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
    )

    overall_confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
    )

    evaluation_reasons: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("status", "draft")
        kwargs.setdefault("overall_confidence", Decimal("0"))
        kwargs.setdefault("evaluation_reasons", [])
        super().__init__(**kwargs)


class ProofEvaluationModel(UUIDModel):
    """Immutable persistence record for a proof evaluation."""

    __tablename__ = "proof_evaluations"

    __table_args__ = (
        Index(
            "ix_proof_evaluations_proof_id",
            "proof_id",
        ),
    )

    proof_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    overall_confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    evaluation_reasons: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault(
            "evaluated_at",
            datetime.now(UTC),
        )
        super().__init__(**kwargs)
