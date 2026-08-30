"""Tests for financial repositories."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.financial import (
    EvidenceLinkModel,
    EvidenceModel,
    FinancialClaimModel,
    FinancialProofModel,
    ProofEvaluationModel,
)
from app.db.repositories.financial import (
    EvidenceLinkRepository,
    EvidenceRepository,
    FinancialClaimRepository,
    FinancialProofRepository,
    ProofEvaluationRepository,
)


def create_session() -> Session:
    """Create an isolated in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_evidence_repository_add_and_get() -> None:
    session = create_session()
    repository = EvidenceRepository(session)

    evidence = EvidenceModel(
        evidence_type="bank_statement",
        source_name="Test Bank",
        received_at=date(2026, 8, 28),
    )

    repository.add(evidence)

    result = repository.get_by_id(evidence.id)

    assert result is not None
    assert result.id == evidence.id
    assert result.source_name == "Test Bank"


def test_evidence_repository_returns_none_for_missing_id() -> None:
    session = create_session()
    repository = EvidenceRepository(session)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_evidence_repository_add_flushes_without_commit() -> None:
    session = create_session()
    repository = EvidenceRepository(session)

    evidence = EvidenceModel(
        evidence_type="payslip",
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )

    returned = repository.add(evidence)

    assert returned is evidence
    assert evidence.id is not None
    assert session.get(EvidenceModel, evidence.id) is evidence


def test_claim_repository_add_get_and_list_by_subject() -> None:
    session = create_session()
    repository = FinancialClaimRepository(session)

    claim_one = FinancialClaimModel(
        claim_type="income",
        subject="Applicant",
    )
    claim_two = FinancialClaimModel(
        claim_type="expense",
        subject="Applicant",
    )
    other_claim = FinancialClaimModel(
        claim_type="income",
        subject="Other Applicant",
    )

    repository.add(claim_one)
    repository.add(claim_two)
    repository.add(other_claim)

    result = repository.get_by_id(claim_one.id)
    claims = repository.list_by_subject("Applicant")

    assert result is not None
    assert result.id == claim_one.id
    assert len(claims) == 2
    assert all(claim.subject == "Applicant" for claim in claims)


def test_claim_repository_returns_none_for_missing_id() -> None:
    session = create_session()
    repository = FinancialClaimRepository(session)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_claim_repository_returns_empty_list_for_unknown_subject() -> None:
    session = create_session()
    repository = FinancialClaimRepository(session)

    claim = FinancialClaimModel(
        claim_type="income",
        subject="Applicant",
    )

    repository.add(claim)

    result = repository.list_by_subject("Unknown Applicant")

    assert result == []


def test_evidence_link_repository() -> None:
    session = create_session()
    repository = EvidenceLinkRepository(session)

    claim_id = uuid4()
    evidence_id = uuid4()

    link = EvidenceLinkModel(
        claim_id=claim_id,
        evidence_id=evidence_id,
    )

    repository.add(link)

    result = repository.get_by_id(link.id)
    links = repository.list_by_claim(claim_id)

    assert result is not None
    assert result.id == link.id
    assert len(links) == 1
    assert links[0].claim_id == claim_id


def test_evidence_link_repository_returns_none_for_missing_id() -> None:
    session = create_session()
    repository = EvidenceLinkRepository(session)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_evidence_link_repository_returns_empty_list_for_unknown_claim() -> None:
    session = create_session()
    repository = EvidenceLinkRepository(session)

    link = EvidenceLinkModel(
        claim_id=uuid4(),
        evidence_id=uuid4(),
    )

    repository.add(link)

    result = repository.list_by_claim(uuid4())

    assert result == []


def test_proof_repository_add_get_and_list_by_subject() -> None:
    session = create_session()
    repository = FinancialProofRepository(session)

    proof = FinancialProofModel(subject="Applicant")
    other_proof = FinancialProofModel(subject="Other Applicant")

    repository.add(proof)
    repository.add(other_proof)

    result = repository.get_by_id(proof.id)
    proofs = repository.list_by_subject("Applicant")

    assert result is not None
    assert result.id == proof.id
    assert len(proofs) == 1
    assert proofs[0].subject == "Applicant"


def test_proof_repository_returns_none_for_missing_id() -> None:
    session = create_session()
    repository = FinancialProofRepository(session)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_proof_repository_returns_empty_list_for_unknown_subject() -> None:
    session = create_session()
    repository = FinancialProofRepository(session)

    proof = FinancialProofModel(subject="Applicant")

    repository.add(proof)

    result = repository.list_by_subject("Unknown Applicant")

    assert result == []


def test_evaluation_repository_lists_history_in_chronological_order() -> None:
    session = create_session()
    repository = ProofEvaluationRepository(session)

    proof_id = uuid4()

    older = ProofEvaluationModel(
        proof_id=proof_id,
        status="ready",
        overall_confidence=Decimal("0.8000"),
        evaluation_reasons=["evaluation_passed"],
        evaluated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    newer = ProofEvaluationModel(
        proof_id=proof_id,
        status="ready",
        overall_confidence=Decimal("0.8000"),
        evaluation_reasons=["evaluation_passed"],
        evaluated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )

    repository.add(newer)
    repository.add(older)
    session.flush()

    result = repository.list_by_proof(proof_id)

    assert [evaluation.id for evaluation in result] == [
        older.id,
        newer.id,
    ]


def test_evaluation_repository_returns_empty_for_unknown_proof() -> None:
    session = create_session()
    repository = ProofEvaluationRepository(session)

    result = repository.list_by_proof(uuid4())

    assert result == []

def test_repository_changes_can_be_rolled_back() -> None:
    session = create_session()
    repository = FinancialProofRepository(session)

    proof = FinancialProofModel(subject="Applicant")
    repository.add(proof)

    proof_id = proof.id

    session.rollback()

    assert session.get(FinancialProofModel, proof_id) is None