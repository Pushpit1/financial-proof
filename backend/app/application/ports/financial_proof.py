from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
    FinancialProof,
    ProofEvaluationHistory,
)


class FinancialProofRepositoryPort(ABC):
    """Persistence boundary for financial proof workflows."""

    @abstractmethod
    def add_proof(self, proof: FinancialProof) -> None:
        """Persist a financial proof."""
        raise NotImplementedError

    @abstractmethod
    def update_proof(self, proof: FinancialProof) -> None:
        """Update an existing financial proof."""
        raise NotImplementedError

    @abstractmethod
    def get_proof(self, proof_id: UUID) -> FinancialProof | None:
        """Retrieve a financial proof."""
        raise NotImplementedError

    @abstractmethod
    def list_proofs(self, subject: str) -> list[FinancialProof]:
        """List proofs for a subject."""
        raise NotImplementedError

    @abstractmethod
    def add_claim(
        self,
        claim: FinancialClaim,
        proof_id: UUID | None = None,
    ) -> None:
        """Persist a financial claim."""
        raise NotImplementedError

    @abstractmethod
    def get_claim(self, claim_id: UUID) -> FinancialClaim | None:
        """Retrieve a financial claim."""
        raise NotImplementedError

    @abstractmethod
    def list_claims(self, subject: str) -> list[FinancialClaim]:
        """List claims for a subject."""
        raise NotImplementedError

    @abstractmethod
    def list_claims_by_proof(
        self,
        proof_id: UUID,
    ) -> list[FinancialClaim]:
        """List claims belonging to a proof."""
        raise NotImplementedError

    @abstractmethod
    def add_evidence(
        self,
        evidence: Evidence,
        proof_id: UUID | None = None,
    ) -> None:
        """Persist evidence."""
        raise NotImplementedError

    @abstractmethod
    def get_evidence(self, evidence_id: UUID) -> Evidence | None:
        """Retrieve evidence."""
        raise NotImplementedError

    @abstractmethod
    def list_evidence_by_proof(
        self,
        proof_id: UUID,
    ) -> list[Evidence]:
        """List evidence belonging to a proof."""
        raise NotImplementedError

    @abstractmethod
    def add_evidence_link(self, link: EvidenceLink) -> None:
        """Persist an evidence link."""
        raise NotImplementedError

    @abstractmethod
    def get_evidence_link(
        self,
        link_id: UUID,
    ) -> EvidenceLink | None:
        """Retrieve an evidence link."""
        raise NotImplementedError

    @abstractmethod
    def list_evidence_links_by_claim(
        self,
        claim_id: UUID,
    ) -> list[EvidenceLink]:
        """List evidence links for a claim."""
        raise NotImplementedError

    @abstractmethod
    def list_evidence_links_by_evidence(
        self,
        evidence_id: UUID,
    ) -> list[EvidenceLink]:
        """List evidence links for evidence."""
        raise NotImplementedError

    @abstractmethod
    def add_evaluation(
        self,
        evaluation: ProofEvaluationHistory,
    ) -> None:
        """Persist an evaluation history record."""
        raise NotImplementedError

    @abstractmethod
    def list_evaluation_history(
        self,
        proof_id: UUID,
    ) -> list[ProofEvaluationHistory]:
        """List evaluation history for a proof."""
        raise NotImplementedError
