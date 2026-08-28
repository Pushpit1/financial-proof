"""Tests for financial persistence models."""

from decimal import Decimal
from uuid import uuid4

from app.db.models.financial import (
    EvidenceLinkModel,
    EvidenceModel,
    FinancialClaimModel,
    FinancialProofModel,
)


def test_evidence_model_defaults() -> None:
    evidence = EvidenceModel(
        evidence_type="bank_statement",
        source_name="Test Bank",
        received_at=__import__("datetime").date(2026, 8, 28),
    )

    assert evidence.id is not None
    assert evidence.status == "received"


def test_financial_claim_model() -> None:
    claim = FinancialClaimModel(
        claim_type="income",
        subject="monthly salary",
        amount=Decimal("80000.00"),
        currency="INR",
    )

    assert claim.id is not None
    assert claim.amount == Decimal("80000.00")
    assert claim.currency == "INR"


def test_evidence_link_model() -> None:
    claim_id = uuid4()
    evidence_id = uuid4()

    link = EvidenceLinkModel(
        claim_id=claim_id,
        evidence_id=evidence_id,
        confidence=Decimal("0.95"),
    )

    assert link.claim_id == claim_id
    assert link.evidence_id == evidence_id


def test_financial_proof_model() -> None:
    proof = FinancialProofModel(subject="Applicant")

    assert proof.id is not None
    assert proof.status == "draft"
    assert proof.overall_confidence == Decimal("0")
