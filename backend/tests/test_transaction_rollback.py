"""Tests for transactional rollback behavior."""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.db.base import Base
from app.db.models.financial import (
    FinancialClaimModel,
    FinancialProofModel,
)
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.enums.financial import ClaimType
from app.domain.models.financial import FinancialClaim, FinancialProof
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
    )


def test_create_proof_rolls_back_when_claim_persistence_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_session()
    unit_of_work = FinancialUnitOfWork(session)
    service = FinancialProofApplicationService(unit_of_work)

    proof = FinancialProof(subject="Applicant")

    original_add = unit_of_work.claims.add
    call_count = 0

    def failing_add(claim: FinancialClaimModel) -> FinancialClaimModel:
        nonlocal call_count
        call_count += 1

        if call_count == 2:
            raise RuntimeError("Simulated claim persistence failure.")

        return original_add(claim)

    monkeypatch.setattr(unit_of_work.claims, "add", failing_add)

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


def test_add_claims_rolls_back_when_claim_persistence_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = create_session()
    unit_of_work = FinancialUnitOfWork(session)
    service = FinancialProofApplicationService(unit_of_work)

    proof = FinancialProof(subject="Applicant")
    service.create_proof(proof, [])

    original_add = unit_of_work.claims.add
    call_count = 0

    def failing_add(claim: FinancialClaimModel) -> FinancialClaimModel:
        nonlocal call_count
        call_count += 1

        if call_count == 2:
            raise RuntimeError("Simulated claim persistence failure.")

        return original_add(claim)

    monkeypatch.setattr(unit_of_work.claims, "add", failing_add)

    claims = [
        make_claim("monthly salary", "0.90"),
        make_claim("annual bonus", "0.80"),
    ]

    with pytest.raises(RuntimeError, match="Simulated claim persistence failure"):
        service.add_claims(proof.id, claims)

    stored_claims = session.query(FinancialClaimModel).all()

    assert stored_claims == []
    assert session.get(FinancialProofModel, proof.id) is not None
