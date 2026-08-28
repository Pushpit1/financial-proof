"""Tests for the financial unit of work."""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.financial import (
    EvidenceModel,
    FinancialClaimModel,
    FinancialProofModel,
)
from app.db.unit_of_work import FinancialUnitOfWork


def create_session() -> Session:
    """Create an isolated in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_unit_of_work_exposes_all_repositories() -> None:
    session = create_session()

    with FinancialUnitOfWork(session) as unit_of_work:
        assert unit_of_work.evidence is not None
        assert unit_of_work.claims is not None
        assert unit_of_work.evidence_links is not None
        assert unit_of_work.proofs is not None


def test_unit_of_work_commits_successful_transaction() -> None:
    session = create_session()

    evidence_id = None

    with FinancialUnitOfWork(session) as unit_of_work:
        evidence = EvidenceModel(
            evidence_type="bank_statement",
            source_name="Test Bank",
            received_at=date(2026, 8, 28),
        )

        unit_of_work.evidence.add(evidence)
        evidence_id = evidence.id

    assert evidence_id is not None

    stored = session.get(EvidenceModel, evidence_id)

    assert stored is not None
    assert stored.source_name == "Test Bank"


def test_unit_of_work_rolls_back_failed_transaction() -> None:
    session = create_session()

    evidence_id = None

    with pytest.raises(RuntimeError):
        with FinancialUnitOfWork(session) as unit_of_work:
            evidence = EvidenceModel(
                evidence_type="bank_statement",
                source_name="Should Roll Back",
                received_at=date(2026, 8, 28),
            )

            unit_of_work.evidence.add(evidence)
            evidence_id = evidence.id

            raise RuntimeError("transaction failed")

    assert evidence_id is not None
    assert session.get(EvidenceModel, evidence_id) is None


def test_unit_of_work_can_coordinate_multiple_repositories() -> None:
    session = create_session()

    with FinancialUnitOfWork(session) as unit_of_work:
        proof = FinancialProofModel(subject="Applicant")

        claim = FinancialClaimModel(
            claim_type="income",
            subject="Applicant",
        )

        unit_of_work.proofs.add(proof)
        unit_of_work.claims.add(claim)

    stored_proof = session.get(FinancialProofModel, proof.id)
    stored_claim = session.get(FinancialClaimModel, claim.id)

    assert stored_proof is not None
    assert stored_claim is not None
    assert stored_proof.subject == "Applicant"
    assert stored_claim.subject == "Applicant"
