from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.db.repositories.financial_proof import (
    SqlAlchemyFinancialProofRepository,
)
from app.domain.enums.financial import (
    ClaimType,
    EvidenceType,
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
    FinancialProof,
    ProofEvaluationHistory,
)
from app.domain.value_objects.financial import ConfidenceScore
from tests.conftest import create_session


def make_claim(subject: str) -> FinancialClaim:
    return FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject=subject,
        confidence=ConfidenceScore(Decimal("0.90")),
    )


def make_evidence(source_name: str) -> Evidence:
    return Evidence(
        evidence_type=EvidenceType.BANK_STATEMENT,
        source_name=source_name,
        received_at=date(2026, 8, 31),
    )


def test_add_and_get_proof() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    proof = FinancialProof(subject="Applicant")

    repository.add_proof(proof)
    session.flush()

    result = repository.get_proof(proof.id)

    assert result is not None
    assert result.id == proof.id
    assert result.subject == "Applicant"
    assert result.status == ProofStatus.DRAFT


def test_update_proof() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    proof = FinancialProof(subject="Applicant")

    repository.add_proof(proof)
    session.flush()

    proof.status = ProofStatus.READY
    proof.overall_confidence = ConfidenceScore(Decimal("0.90"))

    from app.domain.enums.financial import EvaluationReason
    from app.domain.services.proof_evaluator import (
        ProofEvaluation,
    )

    proof.apply_evaluation(
        ProofEvaluation(
            status=ProofStatus.READY,
            overall_confidence=ConfidenceScore(Decimal("0.90")),
            reasons=(EvaluationReason.EVALUATION_PASSED,),
        )
    )

    repository.update_proof(proof)
    session.flush()

    result = repository.get_proof(proof.id)

    assert result is not None
    assert result.status == ProofStatus.READY
    assert result.overall_confidence.value == Decimal("0.90")
    assert result.evaluation_reasons == ["evaluation_passed"]


def test_update_missing_proof_raises() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    proof = FinancialProof(subject="Missing")

    with pytest.raises(ValueError, match="was not found"):
        repository.update_proof(proof)


def test_list_proofs_filters_by_subject() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    first = FinancialProof(subject="Applicant")
    second = FinancialProof(subject="Applicant")
    other = FinancialProof(subject="Other")

    repository.add_proof(first)
    repository.add_proof(second)
    repository.add_proof(other)
    session.flush()

    results = repository.list_proofs("Applicant")

    assert {proof.id for proof in results} == {first.id, second.id}
    assert all(proof.subject == "Applicant" for proof in results)


def test_missing_proof_returns_none() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    proof = repository.get_proof(
        FinancialProof(subject="Temporary").id,
    )

    assert proof is None


def test_add_and_get_claim() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    claim = make_claim("monthly salary")

    repository.add_claim(claim)
    session.flush()

    result = repository.get_claim(claim.id)

    assert result is not None
    assert result.id == claim.id
    assert result.subject == "monthly salary"
    assert result.claim_type == ClaimType.INCOME


def test_list_claims_filters_by_subject() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    first = make_claim("Applicant")
    second = make_claim("Applicant")
    other = make_claim("Other")

    repository.add_claim(first)
    repository.add_claim(second)
    repository.add_claim(other)
    session.flush()

    results = repository.list_claims("Applicant")

    assert [claim.id for claim in results] == [first.id, second.id]


def test_list_claims_by_proof() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    proof = FinancialProof(subject="Applicant")
    claim_one = make_claim("salary")
    claim_two = make_claim("bonus")
    unrelated = make_claim("other")

    repository.add_proof(proof)
    repository.add_claim(claim_one, proof.id)
    repository.add_claim(claim_two, proof.id)
    repository.add_claim(unrelated)
    session.flush()

    results = repository.list_claims_by_proof(proof.id)

    assert {claim.id for claim in results} == {claim_one.id, claim_two.id}


def test_missing_claim_returns_none() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    result = repository.get_claim(FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="Missing",
    ).id)

    assert result is None


def test_add_and_get_evidence() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    evidence = make_evidence("Test Bank")

    repository.add_evidence(evidence)
    session.flush()

    result = repository.get_evidence(evidence.id)

    assert result is not None
    assert result.id == evidence.id
    assert result.source_name == "Test Bank"


def test_list_evidence_by_proof() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    proof = FinancialProof(subject="Applicant")
    first = make_evidence("Bank A")
    second = make_evidence("Bank B")
    unrelated = make_evidence("Other Bank")

    repository.add_proof(proof)
    repository.add_evidence(first, proof.id)
    repository.add_evidence(second, proof.id)
    repository.add_evidence(unrelated)
    session.flush()

    results = repository.list_evidence_by_proof(proof.id)

    assert {item.id for item in results} == {first.id, second.id}


def test_missing_evidence_returns_none() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    result = repository.get_evidence(
        make_evidence("Missing").id,
    )

    assert result is None


def test_add_and_get_evidence_link() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    claim = make_claim("salary")
    evidence = make_evidence("Test Bank")

    repository.add_claim(claim)
    repository.add_evidence(evidence)
    session.flush()

    link = EvidenceLink(
        claim_id=claim.id,
        evidence_id=evidence.id,
        verification_status=VerificationStatus.SUPPORTED,
        confidence=ConfidenceScore(Decimal("0.95")),
        explanation="Bank statement supports salary.",
    )

    repository.add_evidence_link(link)
    session.flush()

    result = repository.get_evidence_link(link.id)

    assert result is not None
    assert result.id == link.id
    assert result.claim_id == claim.id
    assert result.evidence_id == evidence.id
    assert result.verification_status == VerificationStatus.SUPPORTED
    assert result.confidence.value == Decimal("0.95")


def test_list_evidence_links_by_claim() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    claim = make_claim("salary")
    evidence_one = make_evidence("Bank A")
    evidence_two = make_evidence("Bank B")

    repository.add_claim(claim)
    repository.add_evidence(evidence_one)
    repository.add_evidence(evidence_two)
    session.flush()

    first = EvidenceLink(
        claim_id=claim.id,
        evidence_id=evidence_one.id,
    )
    second = EvidenceLink(
        claim_id=claim.id,
        evidence_id=evidence_two.id,
    )

    repository.add_evidence_link(first)
    repository.add_evidence_link(second)
    session.flush()

    results = repository.list_evidence_links_by_claim(claim.id)

    assert [link.id for link in results] == [first.id, second.id]


def test_list_evidence_links_by_evidence() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    claim_one = make_claim("salary")
    claim_two = make_claim("bonus")
    evidence = make_evidence("Test Bank")

    repository.add_claim(claim_one)
    repository.add_claim(claim_two)
    repository.add_evidence(evidence)
    session.flush()

    first = EvidenceLink(
        claim_id=claim_one.id,
        evidence_id=evidence.id,
    )
    second = EvidenceLink(
        claim_id=claim_two.id,
        evidence_id=evidence.id,
    )

    repository.add_evidence_link(first)
    repository.add_evidence_link(second)
    session.flush()

    results = repository.list_evidence_links_by_evidence(evidence.id)

    assert [link.id for link in results] == [first.id, second.id]


def test_missing_evidence_link_returns_none() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    link = EvidenceLink(
        claim_id=FinancialClaim(
            claim_type=ClaimType.INCOME,
            subject="Missing",
        ).id,
        evidence_id=make_evidence("Missing").id,
    )

    result = repository.get_evidence_link(link.id)

    assert result is None


def test_add_and_list_evaluation_history() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    proof = FinancialProof(subject="Applicant")
    repository.add_proof(proof)
    session.flush()

    first_time = datetime(2026, 8, 30, 10, 0, tzinfo=UTC)
    second_time = datetime(2026, 8, 31, 10, 0, tzinfo=UTC)

    first = ProofEvaluationHistory(
        proof_id=proof.id,
        status=ProofStatus.NEEDS_REVIEW,
        overall_confidence=ConfidenceScore(Decimal("0.60")),
        evaluation_reasons=("unverified_claim",),
        evaluated_at=first_time,
    )

    second = ProofEvaluationHistory(
        proof_id=proof.id,
        status=ProofStatus.READY,
        overall_confidence=ConfidenceScore(Decimal("0.90")),
        evaluation_reasons=("evaluation_passed",),
        evaluated_at=second_time,
    )

    repository.add_evaluation(first)
    repository.add_evaluation(second)
    session.flush()

    results = repository.list_evaluation_history(proof.id)

    assert [item.id for item in results] == [first.id, second.id]
    assert results[0].status == ProofStatus.NEEDS_REVIEW
    assert results[1].status == ProofStatus.READY


def test_evaluation_history_isolated_by_proof() -> None:
    session = create_session()
    repository = SqlAlchemyFinancialProofRepository(session)

    first_proof = FinancialProof(subject="First")
    second_proof = FinancialProof(subject="Second")

    repository.add_proof(first_proof)
    repository.add_proof(second_proof)
    session.flush()

    evaluation = ProofEvaluationHistory(
        proof_id=first_proof.id,
        status=ProofStatus.READY,
        overall_confidence=ConfidenceScore(Decimal("0.90")),
        evaluation_reasons=("evaluation_passed",),
        evaluated_at=datetime(2026, 8, 31, tzinfo=UTC),
    )

    repository.add_evaluation(evaluation)
    session.flush()

    results = repository.list_evaluation_history(first_proof.id)

    assert len(results) == 1
    assert results[0].id == evaluation.id
    assert results[0].proof_id == evaluation.proof_id
    assert results[0].status == evaluation.status
    assert results[0].overall_confidence == evaluation.overall_confidence
    assert results[0].evaluation_reasons == evaluation.evaluation_reasons
    assert results[0].evaluated_at.replace(tzinfo=UTC) == evaluation.evaluated_at

    assert repository.list_evaluation_history(second_proof.id) == []


