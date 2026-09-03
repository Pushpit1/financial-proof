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
from tests.support_database_lifecycle import register_session


def create_session() -> Session:
    """Create an isolated in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return register_session(Session(engine), engine)


def test_unit_of_work_exposes_financial_proof_repository() -> None:
    session = create_session()

    with FinancialUnitOfWork(session) as unit_of_work:
        assert unit_of_work.financial_proofs is not None
        assert unit_of_work.contracts is not None
        assert unit_of_work.decisions is not None


def test_unit_of_work_flushes_pending_changes_without_committing() -> None:
    session = create_session()

    with FinancialUnitOfWork(session) as unit_of_work:
        evidence = EvidenceModel(
            evidence_type="bank_statement",
            source_name="Flush Test Bank",
            received_at=date(2026, 8, 28),
        )

        unit_of_work.financial_proofs.session.add(evidence)
        unit_of_work.flush()

        assert session.get(EvidenceModel, evidence.id) is not None

        session.rollback()

    assert session.get(EvidenceModel, evidence.id) is None


def test_unit_of_work_commits_successful_transaction() -> None:
    session = create_session()

    evidence_id = None

    with FinancialUnitOfWork(session) as unit_of_work:
        evidence = EvidenceModel(
            evidence_type="bank_statement",
            source_name="Test Bank",
            received_at=date(2026, 8, 28),
        )

        evidence_id = evidence.id
        unit_of_work.financial_proofs.session.add(evidence)

    assert evidence_id is not None
    assert session.get(EvidenceModel, evidence_id) is not None


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

            evidence_id = evidence.id
            unit_of_work.financial_proofs.session.add(evidence)

            raise RuntimeError("Simulated transaction failure.")

    assert evidence_id is not None
    assert session.get(EvidenceModel, evidence_id) is None


def test_unit_of_work_can_coordinate_multiple_financial_proof_records() -> None:
    session = create_session()

    proof_id = None
    claim_id = None

    with FinancialUnitOfWork(session) as unit_of_work:
        proof = FinancialProofModel(subject="Applicant")

        claim = FinancialClaimModel(
            claim_type="income",
            subject="Applicant",
        )

        proof_id = proof.id
        claim_id = claim.id

        unit_of_work.financial_proofs.session.add(proof)
        unit_of_work.financial_proofs.session.add(claim)

    assert proof_id is not None
    assert claim_id is not None
    assert session.get(FinancialProofModel, proof_id) is not None
    assert session.get(FinancialClaimModel, claim_id) is not None



