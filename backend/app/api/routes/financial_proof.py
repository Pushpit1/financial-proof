from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_financial_proof_service
from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.schemas.financial_proof import (
    EvidenceLinkResponse,
    EvidenceResponse,
    FinancialClaimResponse,
    FinancialProofAggregateResponse,
    FinancialProofResponse,
)

router = APIRouter(prefix="/proofs", tags=["financial-proof"])


@router.get(
    "/{proof_id}",
    response_model=FinancialProofAggregateResponse,
)
async def get_proof(
    proof_id: UUID,
    service: FinancialProofApplicationService = Depends(
        get_financial_proof_service
    ),  # noqa: B008
) -> FinancialProofAggregateResponse:
    """Return a complete financial proof aggregate."""
    aggregate = service.get_proof_aggregate(proof_id)

    if aggregate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Financial proof {proof_id} was not found.",
        )

    proof = aggregate.proof

    return FinancialProofAggregateResponse(
        proof=FinancialProofResponse(
            id=proof.id,
            subject=proof.subject,
            status=proof.status.value,
            overall_confidence=proof.overall_confidence.value,
        ),
        claims=[
            FinancialClaimResponse(
                id=claim.id,
                claim_type=claim.claim_type.value,
                subject=claim.subject,
                amount=claim.amount.amount if claim.amount else None,
                currency=claim.amount.currency if claim.amount else None,
                verification_status=claim.verification_status.value,
                confidence=claim.confidence.value,
                confidence_level=claim.confidence_level.value,
            )
            for claim in aggregate.claims
        ],
        evidence=[
            EvidenceResponse(
                id=evidence.id,
                evidence_type=evidence.evidence_type.value,
                source_name=evidence.source_name,
                received_at=evidence.received_at,
                status=evidence.status.value,
                checksum=evidence.checksum,
                source_reference=evidence.source_reference,
            )
            for evidence in aggregate.evidence
        ],
        evidence_links=[
            EvidenceLinkResponse(
                id=link.id,
                claim_id=link.claim_id,
                evidence_id=link.evidence_id,
                verification_status=link.verification_status.value,
                confidence=link.confidence.value,
                explanation=link.explanation,
            )
            for link in aggregate.evidence_links
        ],
    )

