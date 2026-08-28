"""Financial proof API routes."""

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

router = APIRouter(
    prefix="/proofs",
    tags=["financial-proofs"],
)


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

    claims = [
        FinancialClaimResponse(
            id=claim.id,
            claim_type=claim.claim_type.value,
            subject=claim.subject,
            amount=(
                claim.amount.amount
                if claim.amount is not None
                else None
            ),
            currency=(
                claim.amount.currency
                if claim.amount is not None
                else None
            ),
            verification_status=claim.verification_status.value,
            confidence=claim.confidence.value,
            confidence_level=claim.confidence_level.value,
        )
        for claim in aggregate.claims
    ]

    evidence = [
        EvidenceResponse(
            id=item.id,
            evidence_type=item.evidence_type.value,
            source_name=item.source_name,
            received_at=item.received_at,
            status=item.status.value,
            checksum=item.checksum,
            source_reference=item.source_reference,
        )
        for item in aggregate.evidence
    ]

    evidence_links = [
        EvidenceLinkResponse(
            id=link.id,
            claim_id=link.claim_id,
            evidence_id=link.evidence_id,
            verification_status=link.verification_status.value,
            confidence=link.confidence.value,
            explanation=link.explanation,
        )
        for link in aggregate.evidence_links
    ]

    return FinancialProofAggregateResponse(
        proof=FinancialProofResponse(
            id=aggregate.proof.id,
            subject=aggregate.proof.subject,
            status=aggregate.proof.status.value,
            overall_confidence=aggregate.proof.overall_confidence.value,
        ),
        claims=claims,
        evidence=evidence,
        evidence_links=evidence_links,
    )
