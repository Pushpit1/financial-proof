from datetime import date
from decimal import Decimal

import pytest

from app.domain.enums.financial import (
    ClaimType,
    ConfidenceLevel,
    EvidenceStatus,
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
from app.domain.value_objects.financial import (
    ConfidenceScore,
    FinancialPeriod,
    Money,
)


def test_money_accepts_valid_amount() -> None:
    money = Money(
        amount=Decimal("80000.00"),
        currency="INR",
    )

    assert money.amount == Decimal("80000.00")
    assert money.currency == "INR"


def test_money_rejects_negative_amount() -> None:
    with pytest.raises(ValueError):
        Money(
            amount=Decimal("-1"),
            currency="INR",
        )


def test_money_rejects_invalid_currency() -> None:
    with pytest.raises(ValueError):
        Money(
            amount=Decimal("100"),
            currency="IN",
        )


def test_financial_period_requires_valid_order() -> None:
    period = FinancialPeriod(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    assert period.start_date < period.end_date


def test_financial_period_rejects_reverse_order() -> None:
    with pytest.raises(ValueError):
        FinancialPeriod(
            start_date=date(2026, 2, 1),
            end_date=date(2026, 1, 1),
        )


def test_confidence_score_requires_zero_to_one() -> None:
    score = ConfidenceScore(Decimal("0.85"))

    assert score.value == Decimal("0.85")


def test_confidence_score_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        ConfidenceScore(Decimal("1.5"))


def test_evidence_defaults_to_received() -> None:
    evidence = Evidence(
        evidence_type=EvidenceType.BANK_STATEMENT,
        source_name="Test Bank",
        received_at=date(2026, 8, 28),
    )

    assert evidence.status == EvidenceStatus.RECEIVED
    assert evidence.checksum is None


def test_financial_claim_defaults_to_unverified() -> None:
    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    assert claim.verification_status == VerificationStatus.UNVERIFIED
    assert claim.confidence.value == Decimal("0")
    assert claim.confidence_level == ConfidenceLevel.VERY_LOW


def test_evidence_link_connects_claim_and_evidence() -> None:
    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
    )

    evidence = Evidence(
        evidence_type=EvidenceType.PAYSLIP,
        source_name="Employer",
        received_at=date(2026, 8, 28),
    )

    link = EvidenceLink(
        claim_id=claim.id,
        evidence_id=evidence.id,
        verification_status=VerificationStatus.SUPPORTED,
        confidence=ConfidenceScore(Decimal("0.95")),
        explanation="Payslip contains the claimed monthly salary.",
    )

    assert link.claim_id == claim.id
    assert link.evidence_id == evidence.id
    assert link.verification_status == VerificationStatus.SUPPORTED


def test_financial_proof_defaults_to_draft() -> None:
    proof = FinancialProof(subject="Applicant")

    assert proof.status == ProofStatus.DRAFT
    assert proof.claim_ids == []
    assert proof.evidence_ids == []
    assert proof.overall_confidence.value == Decimal("0")