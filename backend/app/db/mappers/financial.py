"""Mappings between financial domain objects and persistence models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.domain.services.proof_evaluator import ProofEvaluation

from app.db.models.financial import (
    EvidenceLinkModel,
    EvidenceModel,
    FinancialClaimModel,
    FinancialContractDecisionModel,
    FinancialContractModel,
    FinancialProofModel,
    ProofEvaluationModel,
)
from app.db.models.financial_guardian_audit import (
    FinancialGuardianAuditRecordModel,
)
from app.domain.enums.financial import (
    ClaimType,
    ConfidenceLevel,
    EvidenceStatus,
    EvidenceType,
    ProofStatus,
    VerificationStatus,
)
from app.domain.enums.financial_guardian import GuardianDecision
from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
    FinancialContract,
    FinancialContractDecision,
    FinancialProof,
    ProofEvaluationHistory,
)
from app.domain.models.financial_guardian_audit import (
    FinancialGuardianAuditRecord,
)
from app.domain.value_objects.financial import ConfidenceScore, Money


def evidence_to_model(
    evidence: Evidence,
    proof_id: UUID | None = None,
) -> EvidenceModel:
    """Convert a domain Evidence into a persistence model."""
    return EvidenceModel(
        id=evidence.id,
        proof_id=proof_id,
        evidence_type=evidence.evidence_type.value,
        source_name=evidence.source_name,
        received_at=evidence.received_at,
        status=evidence.status.value,
        checksum=evidence.checksum,
        source_reference=evidence.source_reference,
    )


def evidence_to_domain(model: EvidenceModel) -> Evidence:
    """Convert a persistence Evidence model into a domain object."""
    return Evidence(
        id=model.id,
        evidence_type=EvidenceType(model.evidence_type),
        source_name=model.source_name,
        received_at=model.received_at,
        status=EvidenceStatus(model.status),
        checksum=model.checksum,
        source_reference=model.source_reference,
    )


def claim_to_model(
    claim: FinancialClaim,
    proof_id: UUID | None = None,
) -> FinancialClaimModel:
    """Convert a domain FinancialClaim into a persistence model."""
    return FinancialClaimModel(
        id=claim.id,
        proof_id=proof_id,
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


def claim_to_domain(model: FinancialClaimModel) -> FinancialClaim:
    """Convert a persistence FinancialClaim model into a domain object."""
    amount = None

    if model.amount is not None and model.currency is not None:
        amount = Money(
            amount=model.amount,
            currency=model.currency,
        )

    return FinancialClaim(
        id=model.id,
        claim_type=ClaimType(model.claim_type),
        subject=model.subject,
        amount=amount,
        verification_status=VerificationStatus(
            model.verification_status
        ),
        confidence=(
            model.confidence
            if isinstance(model.confidence, ConfidenceScore)
            else ConfidenceScore(model.confidence)
        ),
        confidence_level=ConfidenceLevel(model.confidence_level),
    )


def evidence_link_to_model(
    link: EvidenceLink,
) -> EvidenceLinkModel:
    """Convert a domain EvidenceLink into a persistence model."""
    return EvidenceLinkModel(
        id=link.id,
        claim_id=link.claim_id,
        evidence_id=link.evidence_id,
        verification_status=link.verification_status.value,
        confidence=link.confidence.value,
        explanation=link.explanation,
        created_at=link.created_at,
    )


def evidence_link_to_domain(
    model: EvidenceLinkModel,
) -> EvidenceLink:
    """Convert a persistence EvidenceLink model into a domain object."""
    return EvidenceLink(
        id=model.id,
        claim_id=model.claim_id,
        evidence_id=model.evidence_id,
        verification_status=VerificationStatus(
            model.verification_status
        ),
        confidence=(
            model.confidence
            if isinstance(model.confidence, ConfidenceScore)
            else ConfidenceScore(model.confidence)
        ),
        explanation=model.explanation,
        created_at=(
            model.created_at.replace(tzinfo=UTC)
            if model.created_at.tzinfo is None
            else model.created_at.astimezone(UTC)
        ),
    )


def proof_to_model(proof: FinancialProof) -> FinancialProofModel:
    """Convert a domain FinancialProof into a persistence model."""
    return FinancialProofModel(
        id=proof.id,
        subject=proof.subject,
        status=proof.status.value,
        overall_confidence=proof.overall_confidence.value,
        evaluation_reasons=[
            reason.value for reason in proof.evaluation_reasons
        ],
    )


def proof_to_domain(model: FinancialProofModel) -> FinancialProof:
    """Convert a persistence FinancialProof model into a domain object."""
    from app.domain.enums.financial import EvaluationReason

    return FinancialProof(
        id=model.id,
        subject=model.subject,
        status=ProofStatus(model.status),
        overall_confidence=ConfidenceScore(
            model.overall_confidence
        ),
        evaluation_reasons=[
            EvaluationReason(reason)
            for reason in model.evaluation_reasons
        ],
    )


def proof_evaluation_to_domain(
    model: ProofEvaluationModel,
) -> ProofEvaluationHistory:
    """Convert a persisted evaluation into a domain history record."""
    return ProofEvaluationHistory(
        id=model.id,
        proof_id=model.proof_id,
        status=ProofStatus(model.status),
        overall_confidence=ConfidenceScore(
            model.overall_confidence
        ),
        evaluation_reasons=tuple(model.evaluation_reasons),
        evaluated_at=model.evaluated_at,
    )


def proof_evaluation_to_model(
    evaluation: ProofEvaluation | ProofEvaluationHistory,
    proof_id: UUID | None = None,
    evaluated_at: datetime | None = None,
) -> ProofEvaluationModel:
    """Convert a proof evaluation into an immutable persistence record."""
    if isinstance(evaluation, ProofEvaluationHistory):
        return ProofEvaluationModel(
            id=evaluation.id,
            proof_id=evaluation.proof_id,
            status=evaluation.status.value,
            overall_confidence=evaluation.overall_confidence.value,
            evaluation_reasons=list(evaluation.evaluation_reasons),
            evaluated_at=evaluation.evaluated_at,
        )

    if proof_id is None:
        raise ValueError(
            "proof_id is required when mapping a ProofEvaluation."
        )

    return ProofEvaluationModel(
        proof_id=proof_id,
        status=evaluation.status.value,
        overall_confidence=evaluation.overall_confidence.value,
        evaluation_reasons=[
            reason.value for reason in evaluation.reasons
        ],
        evaluated_at=evaluated_at,
    )

def financial_contract_to_model(
    contract: FinancialContract,
) -> FinancialContractModel:
    """Convert a domain financial contract into persistence."""
    return FinancialContractModel(
        id=contract.id,
        name=contract.name,
        version=contract.version,
        minimum_confidence=(
            contract.minimum_confidence.value
            if hasattr(contract.minimum_confidence, "value")
            else contract.minimum_confidence
        ),
        minimum_supported_claim_ratio=(
            contract.minimum_supported_claim_ratio
        ),
        required_claim_types=[
            (
                claim_type.value
                if hasattr(claim_type, "value")
                else claim_type
            )
            for claim_type in contract.required_claim_types
        ],
    )

def financial_contract_to_domain(
    model: FinancialContractModel,
) -> FinancialContract:
    """Convert persisted financial contract into the domain."""
    return FinancialContract(
        id=model.id,
        name=model.name,
        version=model.version,
        minimum_confidence=ConfidenceScore(
            model.minimum_confidence
        ),
        minimum_supported_claim_ratio=(
            model.minimum_supported_claim_ratio
        ),
        required_claim_types=tuple(
            ClaimType(claim_type)
            for claim_type in model.required_claim_types
        ),
    )


def financial_contract_decision_to_model(
    decision: FinancialContractDecision,
) -> FinancialContractDecisionModel:
    """Convert contract decision to persistence model."""
    return FinancialContractDecisionModel(
        id=decision.id,
        contract_id=decision.contract_id,
        passed=decision.passed,
        reason_codes=list(decision.reason_codes),
        violation_count=decision.violation_count,
        evaluated_at=decision.evaluated_at,
    )


def financial_contract_decision_to_domain(
    model: FinancialContractDecisionModel,
) -> FinancialContractDecision:
    """Convert persisted decision into a domain record."""
    return FinancialContractDecision(
        id=model.id,
        contract_id=model.contract_id,
        passed=model.passed,
        reason_codes=tuple(model.reason_codes),
        violation_count=model.violation_count,
        evaluated_at=model.evaluated_at,
    )












def financial_guardian_audit_to_model(
    record: FinancialGuardianAuditRecord,
) -> FinancialGuardianAuditRecordModel:
    """Convert a guardian audit domain record to persistence."""
    return FinancialGuardianAuditRecordModel(
        id=record.id,
        actor_id=record.actor_id,
        operation=record.operation,
        rule=record.rule,
        decision=record.decision.value,
        reason=record.reason,
        created_at=record.created_at,
    )


def financial_guardian_audit_to_domain(
    model: FinancialGuardianAuditRecordModel,
) -> FinancialGuardianAuditRecord:
    """Convert a persisted guardian audit record to domain."""
    return FinancialGuardianAuditRecord(
        id=model.id,
        actor_id=model.actor_id,
        operation=model.operation,
        rule=model.rule,
        decision=GuardianDecision(model.decision),
        reason=model.reason,
        created_at=model.created_at,
    )

