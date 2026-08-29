from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.financial import ProofEvaluationModel
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.enums.financial import (
    ClaimType,
    VerificationStatus,
)
from app.domain.models.financial import FinancialClaim, FinancialProof
from app.domain.services.proof_evaluator import ProofEvaluator
from app.domain.value_objects.financial import ConfidenceScore


def make_claim(confidence: str) -> FinancialClaim:
    return FinancialClaim(
        claim_type=ClaimType.INCOME,
        subject="Monthly salary",
        confidence=ConfidenceScore(Decimal(confidence)),
        verification_status=VerificationStatus.VERIFIED,
    )


def test_evaluate_proof_creates_audit_record(db: Session) -> None:
    from app.application.services.financial_proof import (
        FinancialProofApplicationService,
    )
    session = db
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session),
        evaluator=ProofEvaluator(),
    )

    proof = FinancialProof(subject="Applicant")
    service.create_proof(
        proof,
        [
            make_claim("0.90"),
            make_claim("0.70"),
        ],
    )

    result = service.evaluate_proof(proof.id)

    assert result is not None

    history = session.query(ProofEvaluationModel).filter(
        ProofEvaluationModel.proof_id == proof.id
    ).all()

    assert len(history) == 1
    assert history[0].status == result.status.value
    assert history[0].overall_confidence == Decimal("0.8000")
    assert history[0].evaluation_reasons == ["evaluation_passed"]


def test_repeated_evaluations_create_multiple_audit_records(
    db: Session,
) -> None:
    from app.application.services.financial_proof import (
        FinancialProofApplicationService,
    )
    session = db
    service = FinancialProofApplicationService(
        FinancialUnitOfWork(session),
        evaluator=ProofEvaluator(),
    )

    proof = FinancialProof(subject="Applicant")
    service.create_proof(
        proof,
        [
            make_claim("0.90"),
            make_claim("0.70"),
        ],
    )

    first = service.evaluate_proof(proof.id)
    second = service.evaluate_proof(proof.id)

    assert first is not None
    assert second is not None

    history = session.query(ProofEvaluationModel).filter(
        ProofEvaluationModel.proof_id == proof.id
    ).all()

    assert len(history) == 2
    assert history[0].status == "ready"
    assert history[1].status == "ready"
    assert history[0].evaluation_reasons == ["evaluation_passed"]
    assert history[1].evaluation_reasons == ["evaluation_passed"]

