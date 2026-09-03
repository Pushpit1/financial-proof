"""Tests for the evidence application workflow."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.core.errors.domain import NotFoundError
from app.db.base import Base
from app.db.models.financial import (
    EvidenceLinkModel,
    EvidenceModel,
    FinancialClaimModel,
)
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.enums.financial import (
    ClaimType,
    EvidenceType,
    VerificationStatus,
)
from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
)
from tests.support_database_lifecycle import register_session


def create_session() -> Session:
    """Create an isolated in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return register_session(Session(engine), engine)


def test_add_evidence_persists_and_returns_evidence() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    evidence = Evidence(
        evidence_type=EvidenceType.BANK_STATEMENT,
        source_name="Test Bank",
        received_at=date(2026, 8, 28),
    )

    result = service.add_evidence(evidence)

    stored = session.get(EvidenceModel, evidence.id)

    assert result == evidence
    assert stored is not None
    assert stored.source_name == "Test Bank"
    assert stored.evidence_type == "bank_statement"


def test_get_evidence_returns_domain_object() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )

    service.add_evidence(evidence)

    result = service.get_evidence(evidence.id)

    assert result == evidence


def test_get_evidence_returns_none_for_missing_id() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    result = service.get_evidence(uuid4())

    assert result is None


def test_add_evidence_link_persists_and_returns_link() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    claim_id = uuid4()
    evidence_id = uuid4()

    link = EvidenceLink(
        claim_id=claim_id,
        evidence_id=evidence_id,
        verification_status=VerificationStatus.SUPPORTED,
        confidence=__import__(
            "app.domain.value_objects.financial",
            fromlist=["ConfidenceScore"],
        ).ConfidenceScore(Decimal("0.95")),
        explanation="Evidence supports the claim.",
    )

    result = service.add_evidence_link(link)

    stored = session.get(EvidenceLinkModel, link.id)

    assert result == link
    assert stored is not None
    assert stored.claim_id == claim_id
    assert stored.evidence_id == evidence_id
    assert stored.verification_status == "supported"


def test_get_evidence_link_returns_domain_object() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    link = EvidenceLink(
        claim_id=uuid4(),
        evidence_id=uuid4(),
    )

    service.add_evidence_link(link)

    result = service.get_evidence_link(link.id)

    assert result == link


def test_get_evidence_link_returns_none_for_missing_id() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    result = service.get_evidence_link(uuid4())

    assert result is None


def test_list_evidence_links_returns_links_for_claim() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    claim_id = uuid4()

    first = EvidenceLink(
        claim_id=claim_id,
        evidence_id=uuid4(),
    )
    second = EvidenceLink(
        claim_id=claim_id,
        evidence_id=uuid4(),
    )
    other = EvidenceLink(
        claim_id=uuid4(),
        evidence_id=uuid4(),
    )

    service.add_evidence_link(first)
    service.add_evidence_link(second)
    service.add_evidence_link(other)

    result = service.list_evidence_links(claim_id)

    assert len(result) == 2
    assert {link.id for link in result} == {first.id, second.id}


def test_evidence_link_preserves_confidence_and_explanation() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    link = EvidenceLink(
        claim_id=uuid4(),
        evidence_id=uuid4(),
        verification_status=VerificationStatus.VERIFIED,
        confidence=__import__(
            "app.domain.value_objects.financial",
            fromlist=["ConfidenceScore"],
        ).ConfidenceScore(Decimal("0.99")),
        explanation="Verified against source document.",
    )

    service.add_evidence_link(link)

    result = service.get_evidence_link(link.id)

    assert result is not None
    assert result.confidence.value == Decimal("0.99")
    assert result.verification_status == VerificationStatus.VERIFIED
    assert result.explanation == "Verified against source document."


def test_evidence_workflow_can_connect_claim_to_evidence() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    session.add(
        FinancialClaimModel(
            id=claim.id,
            claim_type="income",
            subject=claim.subject,
        )
    )
    session.commit()

    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )

    service.add_evidence(evidence)

    link = EvidenceLink(
        claim_id=claim.id,
        evidence_id=evidence.id,
        verification_status=VerificationStatus.SUPPORTED,
        explanation="Payslip supports monthly salary.",
    )

    service.add_evidence_link(link)

    links = service.list_evidence_links(claim.id)

    assert len(links) == 1
    assert links[0].claim_id == claim.id
    assert links[0].evidence_id == evidence.id
def test_attach_evidence_to_claim_persists_link() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    session.add(
        FinancialClaimModel(
            id=claim.id,
            claim_type="income",
            subject=claim.subject,
        )
    )
    session.commit()

    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )
    service.add_evidence(evidence)

    link = EvidenceLink(
        claim_id=claim.id,
        evidence_id=evidence.id,
        verification_status=VerificationStatus.SUPPORTED,
        confidence=__import__(
            "app.domain.value_objects.financial",
            fromlist=["ConfidenceScore"],
        ).ConfidenceScore(Decimal("0.95")),
        explanation="Payslip supports monthly salary.",
    )

    result = service.attach_evidence_to_claim(
        claim.id,
        evidence.id,
        link,
    )

    assert result == link

    stored = session.get(EvidenceLinkModel, link.id)

    assert stored is not None
    assert stored.claim_id == claim.id
    assert stored.evidence_id == evidence.id


def test_attach_evidence_to_claim_rejects_missing_claim() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )
    service.add_evidence(evidence)

    missing_claim_id = uuid4()

    link = EvidenceLink(
        claim_id=missing_claim_id,
        evidence_id=evidence.id,
    )

    with pytest.raises(NotFoundError):
        service.attach_evidence_to_claim(
            missing_claim_id,
            evidence.id,
            link,
        )

    assert session.query(EvidenceLinkModel).count() == 0


def test_attach_evidence_to_claim_rejects_missing_evidence() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    session.add(
        FinancialClaimModel(
            id=claim.id,
            claim_type="income",
            subject=claim.subject,
        )
    )
    session.commit()

    missing_evidence_id = uuid4()

    link = EvidenceLink(
        claim_id=claim.id,
        evidence_id=missing_evidence_id,
    )

    with pytest.raises(NotFoundError):
        service.attach_evidence_to_claim(
            claim.id,
            missing_evidence_id,
            link,
        )

    assert session.query(EvidenceLinkModel).count() == 0
def test_attach_evidence_to_claim_rejects_mismatched_claim_id() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    session.add(
        FinancialClaimModel(
            id=claim.id,
            claim_type="income",
            subject=claim.subject,
        )
    )
    session.commit()

    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )
    service.add_evidence(evidence)

    different_claim_id = uuid4()

    link = EvidenceLink(
        claim_id=different_claim_id,
        evidence_id=evidence.id,
    )

    with pytest.raises(ValueError, match="claim_id"):
        service.attach_evidence_to_claim(
            claim.id,
            evidence.id,
            link,
        )

    assert session.query(EvidenceLinkModel).count() == 0


def test_attach_evidence_to_claim_rejects_mismatched_evidence_id() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    session.add(
        FinancialClaimModel(
            id=claim.id,
            claim_type="income",
            subject=claim.subject,
        )
    )
    session.commit()

    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )
    service.add_evidence(evidence)

    different_evidence_id = uuid4()

    link = EvidenceLink(
        claim_id=claim.id,
        evidence_id=different_evidence_id,
    )

    with pytest.raises(ValueError, match="evidence_id"):
        service.attach_evidence_to_claim(
            claim.id,
            evidence.id,
            link,
        )

    assert session.query(EvidenceLinkModel).count() == 0
def test_attach_evidence_to_claim_rolls_back_when_link_persistence_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_session()
    unit_of_work = FinancialUnitOfWork(session)
    service = FinancialProofApplicationService(unit_of_work)

    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    session.add(
        FinancialClaimModel(
            id=claim.id,
            claim_type="income",
            subject=claim.subject,
        )
    )
    session.commit()

    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )
    service.add_evidence(evidence)

    link = EvidenceLink(
        claim_id=claim.id,
        evidence_id=evidence.id,
        verification_status=VerificationStatus.SUPPORTED,
        explanation="Payslip supports monthly salary.",
    )

    original_add = unit_of_work.financial_proofs.add_evidence_link

    def failing_add(
        evidence_link: EvidenceLinkModel,
    ) -> EvidenceLinkModel:
        original_add(evidence_link)
        raise RuntimeError("Simulated evidence-link persistence failure.")

    monkeypatch.setattr(
        unit_of_work.financial_proofs,
        "add_evidence_link",
        failing_add,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated evidence-link persistence failure",
    ):
        service.attach_evidence_to_claim(
            claim.id,
            evidence.id,
            link,
        )

    assert session.query(EvidenceLinkModel).count() == 0
def test_list_evidence_links_returns_empty_for_claim_without_links() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    session.add(
        FinancialClaimModel(
            id=claim.id,
            claim_type="income",
            subject=claim.subject,
        )
    )
    session.commit()

    result = service.list_evidence_links(claim.id)

    assert result == []


def test_attach_evidence_to_claim_rejects_duplicate_link() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    session.add(
        FinancialClaimModel(
            id=claim.id,
            claim_type="income",
            subject=claim.subject,
        )
    )
    session.commit()

    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )

    service.add_evidence(evidence)

    link = EvidenceLink(
        claim_id=claim.id,
        evidence_id=evidence.id,
        verification_status=VerificationStatus.SUPPORTED,
        explanation="Supports salary claim.",
    )

    service.attach_evidence_to_claim(
        link.claim_id,
        link.evidence_id,
        link,
    )

    with pytest.raises(ValueError, match="already linked"):
            service.attach_evidence_to_claim(
                claim.id,
                evidence.id,
                EvidenceLink(
                    claim_id=claim.id,
                    evidence_id=evidence.id,
                    verification_status=VerificationStatus.SUPPORTED,
                    explanation="Duplicate link.",
                ),
            )

    assert len(service.list_evidence_links(claim.id)) == 1





