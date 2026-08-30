"""Financial proof API routes."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_financial_proof_service
from app.application.services.financial_proof import (
    FinancialProofApplicationService,
)
from app.core.errors.domain import NotFoundError
from app.domain.enums.financial import EvidenceStatus
from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
    FinancialProof,
)
from app.domain.value_objects.financial import ConfidenceScore, Money
from app.schemas.financial_proof import (
    EvidenceLinkCreateRequest,
    EvidenceLinkResponse,
    EvidenceResponse,
    FinancialClaimResponse,
    FinancialProofAggregateResponse,
    FinancialProofCreateRequest,
    FinancialProofResponse,
    ProofEvaluationResponse,
)

router = APIRouter(prefix="/proofs", tags=["financial-proof"])


@router.get(
    "",
    response_model=list[FinancialProofResponse],
)
async def list_proofs(
    subject: str,
    service: FinancialProofApplicationService = Depends(  # noqa: B008
        get_financial_proof_service
    ),
) -> list[FinancialProofResponse]:
    """List financial proofs belonging to a subject."""
    proofs = service.list_proofs(subject)

    return [
        _proof_to_response(proof)
        for proof in proofs
    ]


def _evaluation_to_response(
    evaluation,
) -> ProofEvaluationResponse:
    """Convert a persisted evaluation into an API response."""
    return ProofEvaluationResponse(
        id=evaluation.id,
        proof_id=evaluation.proof_id,
        status=evaluation.status,
        overall_confidence=evaluation.overall_confidence.value,
        evaluation_reasons=evaluation.evaluation_reasons,
        evaluated_at=evaluation.evaluated_at,
    )


def _claim_to_response(claim: FinancialClaim) -> FinancialClaimResponse:
    """Convert a domain claim into an API response."""
    return FinancialClaimResponse(
        id=claim.id,
        claim_type=claim.claim_type.value,
        subject=claim.subject,
        amount=claim.amount.amount if claim.amount else None,
        currency=claim.amount.currency if claim.amount else None,
        verification_status=claim.verification_status.value,
        confidence=claim.confidence.value,
        confidence_level=claim.confidence_level.value,
    )


def _evidence_to_response(evidence: Evidence) -> EvidenceResponse:
    """Convert domain evidence into an API response."""
    return EvidenceResponse(
        id=evidence.id,
        evidence_type=evidence.evidence_type.value,
        source_name=evidence.source_name,
        received_at=evidence.received_at,
        status=evidence.status.value,
        checksum=evidence.checksum,
        source_reference=evidence.source_reference,
    )


def _evidence_link_to_response(
    link: EvidenceLink,
) -> EvidenceLinkResponse:
    """Convert a domain evidence link into an API response."""
    return EvidenceLinkResponse(
        id=link.id,
        claim_id=link.claim_id,
        evidence_id=link.evidence_id,
        verification_status=link.verification_status.value,
        confidence=link.confidence.value,
        explanation=link.explanation,
    )


def _proof_to_response(proof: FinancialProof) -> FinancialProofResponse:
    """Convert a domain proof into an API response."""
    return FinancialProofResponse(
        id=proof.id,
        subject=proof.subject,
        status=proof.status.value,
        overall_confidence=proof.overall_confidence.value,
        evaluation_reasons=proof.evaluation_reasons,
    )


@router.post(
    "",
    response_model=FinancialProofAggregateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_proof(
    request: FinancialProofCreateRequest,
    service: FinancialProofApplicationService = Depends(get_financial_proof_service),  # noqa: B008
) -> FinancialProofAggregateResponse:
    """Create a complete financial proof aggregate."""
    proof = FinancialProof(
        id=request.id or uuid4(),
        subject=request.subject,
    )

    claims: list[FinancialClaim] = []

    for item in request.claims:
        amount = None

        if item.amount is not None and item.currency is not None:
            amount = Money(
                amount=item.amount,
                currency=item.currency,
            )

        claims.append(
            FinancialClaim(
                id=item.id,
                claim_type=item.claim_type,
                subject=item.subject,
                amount=amount,
                verification_status=item.verification_status,
                confidence=ConfidenceScore(item.confidence),
                confidence_level=item.confidence_level,
            )
        )

    evidence = [
        Evidence(
            id=item.id,
            evidence_type=item.evidence_type,
            source_name=item.source_name,
            received_at=item.received_at,
            status=EvidenceStatus(item.status),
            checksum=item.checksum,
            source_reference=item.source_reference,
        )
        for item in request.evidence
    ]

    evidence_links = [
        EvidenceLink(
            id=item.id,
            claim_id=item.claim_id,
            evidence_id=item.evidence_id,
            verification_status=item.verification_status,
            confidence=ConfidenceScore(item.confidence),
            explanation=item.explanation,
        )
        for item in request.evidence_links
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
            detail="Financial proof was created but could not be retrieved.",
        )

    return FinancialProofAggregateResponse(
        proof=_proof_to_response(aggregate.proof),
        claims=[
            _claim_to_response(claim)
            for claim in aggregate.claims
        ],
        evidence=[
            _evidence_to_response(item)
            for item in aggregate.evidence
        ],
        evidence_links=[
            _evidence_link_to_response(link)
            for link in aggregate.evidence_links
        ],
    )


@router.get(
    "/{proof_id}",
    response_model=FinancialProofAggregateResponse,
)
async def get_proof(
    proof_id: UUID,
    service: FinancialProofApplicationService = Depends(get_financial_proof_service),  # noqa: B008
) -> FinancialProofAggregateResponse:
    """Return a complete financial proof aggregate."""
    aggregate = service.get_proof_aggregate(proof_id)

    if aggregate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Financial proof {proof_id} was not found.",
        )

    return FinancialProofAggregateResponse(
        proof=_proof_to_response(aggregate.proof),
        claims=[
            _claim_to_response(claim)
            for claim in aggregate.claims
        ],
        evidence=[
            _evidence_to_response(item)
            for item in aggregate.evidence
        ],
        evidence_links=[
            _evidence_link_to_response(link)
            for link in aggregate.evidence_links
        ],
    )


@router.get(
    "/evidence/{evidence_id}/links",
    response_model=list[EvidenceLinkResponse],
)
async def list_evidence_links_by_evidence(
    evidence_id: UUID,
    service: FinancialProofApplicationService = Depends(  # noqa: B008
        get_financial_proof_service
    ),
) -> list[EvidenceLinkResponse]:
    """Return evidence links belonging to an evidence record."""
    evidence = service.get_evidence(evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence {evidence_id} was not found.",
        )

    links = service.list_evidence_links_by_evidence(evidence_id)

    return [_evidence_link_to_response(link) for link in links]

@router.post(
    "/claims/{claim_id}/evidence/{evidence_id}",
    response_model=EvidenceLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_evidence_to_claim(
    claim_id: UUID,
    evidence_id: UUID,
    request: EvidenceLinkCreateRequest,
    service: FinancialProofApplicationService = Depends(  # noqa: B008
        get_financial_proof_service
    ),
) -> EvidenceLinkResponse:
    """Attach existing evidence to an existing financial claim."""
    link = EvidenceLink(
        id=request.id or uuid4(),
        claim_id=request.claim_id,
        evidence_id=request.evidence_id,
        verification_status=request.verification_status,
        confidence=ConfidenceScore(request.confidence),
        explanation=request.explanation,
    )

    try:
        attached = service.attach_evidence_to_claim(
            claim_id=claim_id,
            evidence_id=evidence_id,
            link=link,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return _evidence_link_to_response(attached)

@router.get(
    "/{proof_id}/evaluations",
    response_model=list[ProofEvaluationResponse],
)
async def list_proof_evaluations(
    proof_id: UUID,
    service: FinancialProofApplicationService = Depends(  # noqa: B008
        get_financial_proof_service
    ),
) -> list[ProofEvaluationResponse]:
    """Return immutable evaluation history for a financial proof."""
    try:
        evaluations = service.list_evaluation_history(proof_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return [
        _evaluation_to_response(evaluation)
        for evaluation in evaluations
    ]


@router.post(
    "/{proof_id}/evaluate",
    response_model=FinancialProofAggregateResponse,
)
async def evaluate_proof(
    proof_id: UUID,
    service: FinancialProofApplicationService = Depends(  # noqa: B008
        get_financial_proof_service
    ),
) -> FinancialProofAggregateResponse:
    """Evaluate and persist the current financial proof state."""
    try:
        proof = service.evaluate_proof(proof_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    if proof is None:
        raise HTTPException(
            status_code=404,
            detail=f"Financial proof {proof_id} was not found.",
        )

    aggregate = service.get_proof_aggregate(proof.id)

    if aggregate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Financial proof {proof_id} was not found.",
        )

    return FinancialProofAggregateResponse(
        proof=_proof_to_response(aggregate.proof),
        claims=[
            _claim_to_response(claim)
            for claim in aggregate.claims
        ],
        evidence=[
            _evidence_to_response(item)
            for item in aggregate.evidence
        ],
        evidence_links=[
            _evidence_link_to_response(link)
            for link in aggregate.evidence_links
        ],
    )
