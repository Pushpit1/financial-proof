"""Tests for transactional rollback behavior."""

from decimal import Decimal
from uuid import UUID

import pytest

from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.db.models.financial import (
    FinancialClaimModel,
    FinancialProofModel,
    ProofEvaluationModel,
)
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.enums.financial import ClaimType
from app.domain.models.financial import FinancialClaim, FinancialProof
from app.domain.value_objects.financial import ConfidenceScore
from tests.conftest import create_session


def make_claim(subject: str, confidence: str) -> FinancialClaim:
    """Create a financial claim for testing."""
    return FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject=subject,
        confidence=ConfidenceScore(Decimal(confidence)),
    )


def test_create_proof_rolls_back_when_claim_persistence_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_session()
    unit_of_work = FinancialUnitOfWork(session)
    service = FinancialProofApplicationService(unit_of_work)

    proof = FinancialProof(subject="Applicant")

    original_add = unit_of_work.financial_proofs.add_claim
    call_count = 0

    def failing_add(
        claim: FinancialClaim,
        proof_id: UUID | None = None,
    ) -> None:
        nonlocal call_count
        call_count += 1

        if call_count == 2:
            raise RuntimeError("Simulated claim persistence failure.")

        return original_add(claim, proof_id)

    monkeypatch.setattr(unit_of_work.financial_proofs, "add_claim", failing_add)

    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
        make_claim("monthly rent", "0.95"),
    ]

    with pytest.raises(RuntimeError, match="Simulated claim persistence failure"):
        service.create_proof(proof, claims)

    assert session.get(FinancialProofModel, proof.id) is None
    assert session.query(FinancialClaimModel).count() == 0


def test_create_proof_persists_everything_when_no_failure_occurs() -> None:
    session = create_session()
    unit_of_work = FinancialUnitOfWork(session)
    service = FinancialProofApplicationService(unit_of_work)

    proof = FinancialProof(subject="Applicant")

    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
    ]

    service.create_proof(proof, claims)

    assert session.get(FinancialProofModel, proof.id) is not None
    assert session.query(FinancialClaimModel).count() == 2

def test_evaluate_proof_rolls_back_when_evaluation_persistence_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_session()
    unit_of_work = FinancialUnitOfWork(session)
    service = FinancialProofApplicationService(unit_of_work)

    proof = FinancialProof(subject="Evaluation Rollback Applicant")
    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.70"),
    ]

    service.create_proof(proof, claims)

    stored_before = session.get(FinancialProofModel, proof.id)

    assert stored_before is not None
    original_status = stored_before.status
    original_confidence = stored_before.overall_confidence
    original_reasons = stored_before.evaluation_reasons

    def failing_add(evaluation) -> None:
        raise RuntimeError("Simulated evaluation persistence failure.")

    monkeypatch.setattr(
        unit_of_work.financial_proofs,
        "add_evaluation",
        failing_add,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated evaluation persistence failure",
    ):
        service.evaluate_proof(proof.id)

    session.expire_all()

    stored_after = session.get(FinancialProofModel, proof.id)

    assert stored_after is not None
    assert stored_after.status == original_status
    assert stored_after.overall_confidence == original_confidence
    assert stored_after.evaluation_reasons == original_reasons

    assert (
        session.query(ProofEvaluationModel)
        .filter(ProofEvaluationModel.proof_id == proof.id)
        .count()
        == 0
    )


def test_add_claims_rolls_back_when_claim_persistence_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_session()
    unit_of_work = FinancialUnitOfWork(session)
    service = FinancialProofApplicationService(unit_of_work)

    proof = FinancialProof(subject="Applicant")
    service.create_proof(proof, [])

    original_add = unit_of_work.financial_proofs.add_claim
    call_count = 0

    def failing_add(
        claim: FinancialClaim,
        proof_id: UUID | None = None,
    ) -> None:
        nonlocal call_count
        call_count += 1

        if call_count == 2:
            raise RuntimeError("Simulated claim persistence failure.")

        return original_add(claim, proof_id)

    monkeypatch.setattr(unit_of_work.financial_proofs, "add_claim", failing_add)

    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
    ]

    with pytest.raises(RuntimeError, match="Simulated claim persistence failure"):
        service.add_claims(proof.id, claims)

    stored_claims = session.query(FinancialClaimModel).all()

    assert stored_claims == []
    assert session.get(FinancialProofModel, proof.id) is not None

