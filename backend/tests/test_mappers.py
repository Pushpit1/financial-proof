"""Tests for financial domain/persistence mappings."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from app.db.mappers.financial import (
    claim_to_domain,
    claim_to_model,
    evidence_to_domain,
    evidence_to_model,
    financial_contract_to_domain,
    financial_contract_to_model,
    proof_evaluation_to_domain,
    proof_evaluation_to_model,
    proof_to_domain,
    proof_to_model,
)
from app.domain.enums.financial import (
    ClaimType,
    EvaluationReason,
    EvidenceStatus,
    EvidenceType,
    ProofStatus,
    VerificationStatus,
)
from app.domain.models.financial import (
    Evidence,
    FinancialClaim,
    FinancialContract,
    FinancialProof,
    ProofEvaluationHistory,
)
from app.domain.services.proof_evaluator import ProofEvaluation
from app.domain.value_objects.financial import (
    ConfidenceScore,
    Money,
)


def test_evidence_mapping_round_trip() -> None:
    evidence = Evidence(
        evidence_type=EvidenceType.BANK_STATEMENT,
        source_name="Test Bank",
        received_at=date(2026, 8, 28),
        status=EvidenceStatus.VERIFIED,
        checksum="abc123",
        source_reference="statement-001",
    )

    model = evidence_to_model(evidence)
    restored = evidence_to_domain(model)

    assert model.id == evidence.id
    assert model.evidence_type == "bank_statement"
    assert restored == evidence


def test_claim_mapping_round_trip() -> None:
    claim = FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="monthly salary",
        amount=Money(
            amount=Decimal("80000.00"),
            currency="INR",
        ),
        verification_status=VerificationStatus.SUPPORTED,
        confidence=ConfidenceScore(Decimal("0.95")),
    )

    model = claim_to_model(claim)
    restored = claim_to_domain(model)

    assert model.id == claim.id
    assert model.amount == Decimal("80000.00")
    assert model.currency == "INR"
    assert restored == claim


def test_claim_mapping_handles_missing_amount() -> None:
    claim = FinancialClaim(
        claim_type=ClaimType.EMPLOYMENT,
        subject="employed",
    )

    model = claim_to_model(claim)
    restored = claim_to_domain(model)

    assert model.amount is None
    assert model.currency is None
    assert restored.amount is None
    assert restored == claim


def test_proof_mapping_round_trip() -> None:
    proof = FinancialProof(
        subject="Applicant",
        status=ProofStatus.READY,
        overall_confidence=ConfidenceScore(
            Decimal("0.92")
        ),
    )

    model = proof_to_model(proof)
    restored = proof_to_domain(model)

    assert model.id == proof.id
    assert model.status == "ready"
    assert restored == proof

def test_proof_evaluation_history_mapping_round_trip() -> None:
    evaluation = ProofEvaluation(
        status=ProofStatus.READY,
        overall_confidence=ConfidenceScore(
            Decimal("0.85")
        ),
        reasons=(
            EvaluationReason.EVALUATION_PASSED,
        ),
    )

    proof_id = UUID("11111111-1111-1111-1111-111111111111")

    model = proof_evaluation_to_model(
        evaluation,
        proof_id=proof_id,
    )
    restored = proof_evaluation_to_domain(model)

    assert model.proof_id == proof_id
    assert model.status == "ready"
    assert model.overall_confidence == Decimal("0.8500")
    assert model.evaluation_reasons == ["evaluation_passed"]

    assert isinstance(restored, ProofEvaluationHistory)
    assert restored.proof_id == proof_id
    assert restored.status == ProofStatus.READY
    assert restored.overall_confidence == ConfidenceScore(
        Decimal("0.85")
    )
    assert restored.evaluation_reasons == (
        "evaluation_passed",
    )
    assert restored.evaluated_at == model.evaluated_at

def test_financial_contract_mapping_round_trip() -> None:
    contract = FinancialContract(
        name="Income Verification Contract",
        version=2,
        minimum_confidence=ConfidenceScore(
            Decimal("0.80")
        ),
        minimum_supported_claim_ratio=Decimal("0.90"),
        required_claim_types=(
            ClaimType.INCOME,
            ClaimType.EMPLOYMENT,
        ),
    )

    model = financial_contract_to_model(contract)
    restored = financial_contract_to_domain(model)

    assert model.id == contract.id
    assert model.name == "Income Verification Contract"
    assert model.version == 2
    assert model.minimum_confidence == Decimal("0.8000")
    assert model.minimum_supported_claim_ratio == Decimal("0.9000")
    assert model.required_claim_types == [
        "income",
        "employment",
    ]

    assert restored == contract
