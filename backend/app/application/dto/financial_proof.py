"""Application read models for financial proofs."""

from dataclasses import dataclass

from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
    FinancialProof,
)


@dataclass(frozen=True)
class FinancialProofAggregate:
    """Complete financial proof aggregate returned by the application layer."""

    proof: FinancialProof
    claims: tuple[FinancialClaim, ...]
    evidence: tuple[Evidence, ...]
    evidence_links: tuple[EvidenceLink, ...]
