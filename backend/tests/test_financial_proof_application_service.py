"""Tests for the financial proof application service."""

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
    FinancialProofModel,
)
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.enums.financial import (
    ClaimType,
    EvaluationReason,
    EvidenceType,
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
    FinancialProof,
)
from app.domain.services.proof_evaluator import (
    ProofEvaluationPolicy,
    ProofEvaluator,
)
from app.domain.value_objects.financial import ConfidenceScore


def create_session() -> Session:
    """Create an isolated in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def make_claim(subject: str, confidence: str) -> FinancialClaim:
    """Create a financial claim for testing."""
    return FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject=subject,
        confidence=ConfidenceScore(Decimal(confidence)),
        verification_status=VerificationStatus.VERIFIED,
    )


def test_create_proof_persists_proof_and_claims() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
    ]

    result = service.create_proof(proof, claims)

    assert result == proof
    assert session.get(FinancialProofModel, proof.id) is not None
    assert session.query(FinancialClaimModel).count() == 2


def test_create_proof_preserves_claim_values() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claim = make_claim("monthly salary", "0.95")

    service.create_proof(proof, [claim])

    stored = session.get(FinancialClaimModel, claim.id)

    assert stored is not None
    assert stored.proof_id == proof.id
    assert stored.claim_type == "income"
    assert stored.subject == "monthly salary"
    assert stored.confidence == Decimal("0.9500")


def test_create_proof_can_persist_empty_claim_list() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")

    service.create_proof(proof, [])

    assert session.get(FinancialProofModel, proof.id) is not None
    assert session.query(FinancialClaimModel).count() == 0


def test_get_proof_returns_existing_proof() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    service.create_proof(proof, [])

    assert service.get_proof(proof.id) == proof


def test_get_proof_returns_none_for_missing_proof() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    assert service.get_proof(uuid4()) is None


def test_list_proofs_returns_proofs_for_subject() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    applicant = FinancialProof(subject="Applicant")
    other = FinancialProof(subject="Other Applicant")

    service.create_proof(applicant, [])
    service.create_proof(other, [])

    result = service.list_proofs("Applicant")

    assert len(result) == 1
    assert result[0].id == applicant.id


def test_get_claim_returns_existing_claim() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claim = make_claim("monthly salary", "0.90")

    service.create_proof(proof, [claim])

    assert service.get_claim(claim.id) == claim


def test_get_claim_returns_none_for_missing_claim() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    assert service.get_claim(uuid4()) is None


def test_list_claims_returns_claims_matching_claim_subject() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
        make_claim("monthly salary", "0.95"),
    ]

    service.create_proof(proof, claims)

    result = service.list_claims("monthly salary")

    assert len(result) == 2
    assert all(
        claim.subject == "monthly salary"
        for claim in result
    )


def test_list_claims_excludes_other_claim_subjects() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    service.create_proof(
        proof,
        [
            make_claim("monthly salary", "0.90"),
            make_claim("annual bonus", "0.80"),
        ],
    )

    result = service.list_claims("monthly rent")

    assert result == []


def test_list_proof_claims_returns_claims_for_proof() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
    ]

    service.create_proof(proof, claims)

    result = service.list_proof_claims(proof.id)

    assert len(result) == 2
    assert {claim.id for claim in result} == {
        claim.id for claim in claims
    }


def test_list_proof_claims_excludes_other_proofs() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    applicant = FinancialProof(subject="Applicant")
    other = FinancialProof(subject="Other Applicant")

    applicant_claim = make_claim("monthly salary", "0.90")
    other_claim = make_claim("monthly salary", "0.80")

    service.create_proof(applicant, [applicant_claim])
    service.create_proof(other, [other_claim])

    result = service.list_proof_claims(applicant.id)

    assert len(result) == 1
    assert result[0].id == applicant_claim.id


def test_add_claims_to_existing_proof() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    service.create_proof(proof, [])

    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
    ]

    result = service.add_claims(proof.id, claims)

    assert result == proof
    assert len(service.list_proof_claims(proof.id)) == 2


def test_add_claims_rejects_missing_proof() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    with pytest.raises(NotFoundError):
        service.add_claims(
            uuid4(),
            [make_claim("monthly salary", "0.90")],
        )

    assert session.query(FinancialClaimModel).count() == 0


def test_create_proof_persists_complete_proof_graph() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
    ]
    evidence = [
        Evidence(
            evidence_type=EvidenceType.PAYSLIP,
            source_name="Employer",
            received_at=date(2026, 8, 28),
        ),
        Evidence(
            evidence_type=EvidenceType.BANK_STATEMENT,
            source_name="Test Bank",
            received_at=date(2026, 8, 28),
        ),
    ]
    links = [
        EvidenceLink(
            claim_id=claims[0].id,
            evidence_id=evidence[0].id,
            verification_status=VerificationStatus.SUPPORTED,
            explanation="Payslip supports salary.",
        ),
        EvidenceLink(
            claim_id=claims[1].id,
            evidence_id=evidence[1].id,
            verification_status=VerificationStatus.SUPPORTED,
            explanation="Bank statement supports bonus.",
        ),
    ]

    result = service.create_proof(
        proof,
        claims,
        evidence,
        links,
    )

    assert result == proof
    assert session.get(FinancialProofModel, proof.id) is not None
    assert session.query(FinancialClaimModel).count() == 2
    assert session.query(EvidenceModel).count() == 2
    assert session.query(EvidenceLinkModel).count() == 2


def test_create_proof_rejects_link_to_claim_outside_proof() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [make_claim("monthly salary", "0.90")]
    evidence = [
        Evidence(
            evidence_type=EvidenceType.PAYSLIP,
            source_name="Employer",
            received_at=date(2026, 8, 28),
        )
    ]
    link = EvidenceLink(
        claim_id=uuid4(),
        evidence_id=evidence[0].id,
    )

    with pytest.raises(ValueError, match="outside this proof"):
        service.create_proof(
            proof,
            claims,
            evidence,
            [link],
        )

    assert session.query(FinancialProofModel).count() == 0
    assert session.query(FinancialClaimModel).count() == 0
    assert session.query(EvidenceModel).count() == 0
    assert session.query(EvidenceLinkModel).count() == 0


def test_create_proof_rejects_link_to_evidence_outside_proof() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [make_claim("monthly salary", "0.90")]
    evidence = [
        Evidence(
            evidence_type=EvidenceType.PAYSLIP,
            source_name="Employer",
            received_at=date(2026, 8, 28),
        )
    ]
    link = EvidenceLink(
        claim_id=claims[0].id,
        evidence_id=uuid4(),
    )

    with pytest.raises(ValueError, match="outside this proof"):
        service.create_proof(
            proof,
            claims,
            evidence,
            [link],
        )

    assert session.query(FinancialProofModel).count() == 0
    assert session.query(FinancialClaimModel).count() == 0
    assert session.query(EvidenceModel).count() == 0
    assert session.query(EvidenceLinkModel).count() == 0


def test_get_proof_aggregate_returns_complete_graph() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
    ]
    evidence = [
        Evidence(
            evidence_type=EvidenceType.PAYSLIP,
            source_name="Employer",
            received_at=date(2026, 8, 28),
        ),
        Evidence(
            evidence_type=EvidenceType.BANK_STATEMENT,
            source_name="Test Bank",
            received_at=date(2026, 8, 28),
        ),
    ]
    links = [
        EvidenceLink(
            claim_id=claims[0].id,
            evidence_id=evidence[0].id,
            verification_status=VerificationStatus.SUPPORTED,
        ),
        EvidenceLink(
            claim_id=claims[1].id,
            evidence_id=evidence[1].id,
            verification_status=VerificationStatus.SUPPORTED,
        ),
    ]

    service.create_proof(
        proof,
        claims,
        evidence,
        links,
    )

    result = service.get_proof_aggregate(proof.id)

    assert result is not None
    assert result.proof.id == proof.id
    assert {claim.id for claim in result.claims} == {
        claim.id for claim in claims
    }
    assert {item.id for item in result.evidence} == {
        item.id for item in evidence
    }
    assert {link.id for link in result.evidence_links} == {
        link.id for link in links
    }


def test_get_proof_aggregate_returns_none_for_missing_proof() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    assert service.get_proof_aggregate(uuid4()) is None


def test_get_proof_aggregate_returns_empty_children_when_no_children_exist() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    service.create_proof(proof, [])

    result = service.get_proof_aggregate(proof.id)

    assert result is not None
    assert result.proof.id == proof.id
    assert result.claims == ()
    assert result.evidence == ()
    assert result.evidence_links == ()


def test_create_proof_rolls_back_when_link_is_invalid() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [make_claim("monthly salary", "0.90")]
    evidence = [
        Evidence(
            evidence_type=EvidenceType.PAYSLIP,
            source_name="Employer",
            received_at=date(2026, 8, 28),
        )
    ]
    invalid_link = EvidenceLink(
        claim_id=claims[0].id,
        evidence_id=uuid4(),
    )

    with pytest.raises(ValueError):
        service.create_proof(
            proof,
            claims,
            evidence,
            [invalid_link],
        )

    assert session.query(FinancialProofModel).count() == 0
    assert session.query(FinancialClaimModel).count() == 0
    assert session.query(EvidenceModel).count() == 0
    assert session.query(EvidenceLinkModel).count() == 0


def test_evaluate_proof_updates_status_and_confidence() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.70"),
    ]

    service.create_proof(proof, claims)

    result = service.evaluate_proof(proof.id)

    assert result is not None
    assert result.id == proof.id
    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.8000")


def test_evaluate_proof_with_no_claims_is_ready_with_zero_confidence() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    service.create_proof(proof, [])

    result = service.evaluate_proof(proof.id)

    assert result is not None
    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0")


def test_evaluate_proof_with_one_claim_uses_claim_confidence() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claim = make_claim("monthly salary", "0.87")

    service.create_proof(proof, [claim])

    result = service.evaluate_proof(proof.id)

    assert result is not None
    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.8700")


def test_evaluate_proof_uses_average_confidence() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.70"),
        make_claim("monthly rent", "0.80"),
    ]

    service.create_proof(proof, claims)

    result = service.evaluate_proof(proof.id)

    assert result is not None
    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.8000")


def test_evaluate_proof_marks_proof_invalid_when_any_claim_is_contradicted() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("verified income", "0.90"),
        make_claim("contradicted income", "0.80"),
        make_claim("other income", "0.70"),
    ]

    claims[1].verification_status = VerificationStatus.CONTRADICTED

    service.create_proof(proof, claims)

    result = service.evaluate_proof(proof.id)

    assert result is not None
    assert result.status == ProofStatus.INVALID


def test_evaluate_proof_persists_status_confidence_and_reasons() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.70"),
    ]

    service.create_proof(proof, claims)

    result = service.evaluate_proof(proof.id)

    assert result is not None
    assert result.status == ProofStatus.READY
    assert result.evaluation_reasons == [
        EvaluationReason.EVALUATION_PASSED
    ]

    stored = session.get(FinancialProofModel, proof.id)

    assert stored is not None
    assert stored.status == ProofStatus.READY.value
    assert stored.overall_confidence == Decimal("0.8000")
    assert stored.evaluation_reasons == ["evaluation_passed"]


def test_evaluate_proof_returns_none_for_missing_proof() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    result = service.evaluate_proof(uuid4())

    assert result is None


def test_evaluate_proof_persists_invalid_status() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("verified income", "0.90"),
        make_claim("contradicted income", "0.20"),
    ]

    claims[0].verification_status = VerificationStatus.VERIFIED
    claims[1].verification_status = VerificationStatus.CONTRADICTED

    service.create_proof(proof, claims)

    result = service.evaluate_proof(proof.id)

    assert result is not None
    assert result.status == ProofStatus.INVALID

    stored = session.get(FinancialProofModel, proof.id)

    assert stored is not None
    assert stored.status == ProofStatus.INVALID.value
    assert stored.evaluation_reasons == ["contradicted_claim"]


def test_evaluate_proof_uses_injected_evaluator_policy() -> None:
    session = create_session()
    evaluator = ProofEvaluator(
        ProofEvaluationPolicy(
            minimum_ready_confidence=Decimal("0.90")
        )
    )
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session),
        evaluator=evaluator,
    )

    proof = FinancialProof(subject="Applicant")
    claims = [
        make_claim("monthly salary", "0.80"),
        make_claim("annual bonus", "0.80"),
    ]

    service.create_proof(proof, claims)

    result = service.evaluate_proof(proof.id)

    assert result is not None
    assert result.status == ProofStatus.NEEDS_REVIEW
    assert result.overall_confidence.value == Decimal("0.80")


def test_default_service_uses_default_evaluator_policy() -> None:
    session = create_session()
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session)
    )

    assert service.evaluator.policy.minimum_ready_confidence == Decimal(
        "0.70"
    )


def test_service_preserves_injected_evaluator() -> None:
    session = create_session()
    evaluator = ProofEvaluator(
        ProofEvaluationPolicy(
            minimum_ready_confidence=Decimal("0.90")
        )
    )

    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session),
        evaluator=evaluator,
    )

    assert service.evaluator is evaluator
