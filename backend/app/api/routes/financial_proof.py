"""Financial proof API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_financial_proof_service
from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.domain.enums.financial import EvidenceStatus
from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
    FinancialProof,
)
from app.domain.value_objects.financial import ConfidenceScore, Money
from app.schemas.financial_proof import (
    EvidenceCreateRequest,
    EvidenceLinkCreateRequest,
    EvidenceLinkResponse,
    EvidenceResponse,
    FinancialClaimCreateRequest,
    FinancialClaimResponse,
    FinancialProofAggregateResponse,
    FinancialProofCreateRequest,
    FinancialProofResponse,
)

router = APIRouter(prefix="/proofs", tags=["financial-proof"])


def _aggregate_response(
    aggregate,
) -> FinancialProofAggregateResponse:
    """Convert an application aggregate into an API response."""
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


def _claim_from_request(
    request: FinancialClaimCreateRequest,
) -> FinancialClaim:
    amount = None

    if request.amount is not None:
        amount = Money(
            amount=request.amount,
            currency=request.currency,
        )

    kwargs = {
        "claim_type": request.claim_type,
        "subject": request.subject,
        "amount": amount,
        "verification_status": request.verification_status,
        "confidence": ConfidenceScore(request.confidence),
        "confidence_level": request.confidence_level,
    }

    if request.id is not None:
        kwargs["id"] = request.id

    return FinancialClaim(**kwargs)


def _evidence_from_request(
    request: EvidenceCreateRequest,
) -> Evidence:
    kwargs = {
        "evidence_type": request.evidence_type,
        "source_name": request.source_name,
        "received_at": request.received_at,
        "status": EvidenceStatus(request.status),
        "checksum": request.checksum,
        "source_reference": request.source_reference,
    }

    if request.id is not None:
        kwargs["id"] = request.id

    return Evidence(**kwargs)


def _link_from_request(
    request: EvidenceLinkCreateRequest,
) -> EvidenceLink:
    kwargs = {
        "claim_id": request.claim_id,
        "evidence_id": request.evidence_id,
        "verification_status": request.verification_status,
        "confidence": ConfidenceScore(request.confidence),
        "explanation": request.explanation,
    }

    if request.id is not None:
        kwargs["id"] = request.id

    return EvidenceLink(**kwargs)


@router.post(
    "",
    response_model=FinancialProofAggregateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_proof(
    request: FinancialProofCreateRequest,
    service: FinancialProofApplicationService = Depends(  # noqa: B008
        get_financial_proof_service
    ),
) -> FinancialProofAggregateResponse:
    """Create a complete financial proof aggregate."""
    proof_kwargs = {"subject": request.subject}

    if request.id is not None:
        proof_kwargs["id"] = request.id

    proof = FinancialProof(**proof_kwargs)

    claims = [
        _claim_from_request(claim)
        for claim in request.claims
    ]
    evidence = [
        _evidence_from_request(item)
        for item in request.evidence
    ]
    evidence_links = [
        _link_from_request(link)
        for link in request.evidence_links
    ]

    service.create_proof(
        proof,
        claims,
        evidence,
        evidence_links,
    )

    aggregate = service.get_proof_aggregate(proof.id)

    if aggregate is None:
        raise HTTPException(
            status_code=500,
            detail="Created financial proof could not be retrieved.",
        )

    return _aggregate_response(aggregate)


@router.get(
    "/{proof_id}",
    response_model=FinancialProofAggregateResponse,
)
async def get_proof(
    proof_id: UUID,
    service: FinancialProofApplicationService = Depends(  # noqa: B008
        get_financial_proof_service
    ),
) -> FinancialProofAggregateResponse:
    """Return a complete financial proof aggregate."""
    aggregate = service.get_proof_aggregate(proof_id)

    if aggregate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Financial proof {proof_id} was not found.",
        )

    return _aggregate_response(aggregate)
