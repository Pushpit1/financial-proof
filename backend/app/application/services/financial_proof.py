"""Application services for financial proof workflows."""

from datetime import UTC, datetime
from uuid import UUID

from app.application.dto.financial_proof import FinancialProofAggregate
from app.core.errors.domain import NotFoundError
from app.db.unit_of_work import FinancialUnitOfWork
from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
    FinancialProof,
    ProofEvaluationHistory,
)
from app.domain.services.proof_evaluator import ProofEvaluator


class FinancialProofApplicationService:
    """Coordinate financial proof persistence as an application operation."""

    def __init__(
        self,
        unit_of_work: FinancialUnitOfWork,
        evaluator: ProofEvaluator | None = None,
    ) -> None:
        self.unit_of_work = unit_of_work
        self.evaluator = evaluator or ProofEvaluator()

    def create_proof(
        self,
        proof: FinancialProof,
        claims: list[FinancialClaim],
        evidence: list[Evidence] | None = None,
        evidence_links: list[EvidenceLink] | None = None,
    ) -> FinancialProof:
        """Persist a complete financial proof atomically."""
        evidence = evidence or []
        evidence_links = evidence_links or []

        with self.unit_of_work:
            self.unit_of_work.financial_proofs.add_proof(proof)

            for claim in claims:
                self.unit_of_work.financial_proofs.add_claim(
                    claim,
                    proof.id,
                )

            for item in evidence:
                self.unit_of_work.financial_proofs.add_evidence(
                    item,
                    proof.id,
                )

            claim_ids = {claim.id for claim in claims}
            evidence_ids = {item.id for item in evidence}

            for link in evidence_links:
                if link.claim_id not in claim_ids:
                    raise ValueError(
                        "Evidence link references a claim "
                        "outside this proof."
                    )

                if link.evidence_id not in evidence_ids:
                    raise ValueError(
                        "Evidence link references evidence "
                        "outside this proof."
                    )

                self.unit_of_work.financial_proofs.add_evidence_link(
                    link
                )

        return proof

    def get_proof_aggregate(
        self,
        proof_id: UUID,
    ) -> FinancialProofAggregate | None:
        """Retrieve a complete financial proof aggregate."""
        proof = self.unit_of_work.financial_proofs.get_proof(proof_id)

        if proof is None:
            return None

        claims = self.unit_of_work.financial_proofs.list_claims_by_proof(
            proof_id
        )

        claim_ids = {claim.id for claim in claims}

        evidence_links: list[EvidenceLink] = []

        for claim_id in claim_ids:
            evidence_links.extend(
                self.unit_of_work.financial_proofs.list_evidence_links_by_claim(
                    claim_id
                )
            )

        evidence = self.unit_of_work.financial_proofs.list_evidence_by_proof(
            proof_id
        )

        return FinancialProofAggregate(
            proof=proof,
            claims=tuple(claims),
            evidence=tuple(evidence),
            evidence_links=tuple(evidence_links),
        )

    def evaluate_proof(
        self,
        proof_id: UUID,
    ) -> FinancialProof | None:
        """Evaluate a proof and persist both current state and history."""
        with self.unit_of_work:
            proof = self.unit_of_work.financial_proofs.get_proof(proof_id)

            if proof is None:
                return None

            claims = (
                self.unit_of_work.financial_proofs.list_claims_by_proof(
                    proof_id
                )
            )

            evaluation = self.evaluator.evaluate(claims)

            proof.apply_evaluation(evaluation)

            evaluated_at = datetime.now(UTC)

            self.unit_of_work.financial_proofs.update_proof(proof)

            self.unit_of_work.financial_proofs.add_evaluation(
                ProofEvaluationHistory(
                    proof_id=proof_id,
                    status=evaluation.status,
                    overall_confidence=evaluation.overall_confidence,
                    evaluation_reasons=tuple(
                        reason.value for reason in evaluation.reasons
                    ),
                    evaluated_at=evaluated_at,
                )
            )

            self.unit_of_work.flush()

            return proof

    def list_evidence_links_by_evidence(
        self,
        evidence_id: UUID,
    ) -> list[EvidenceLink]:
        """List evidence links belonging to evidence."""
        with self.unit_of_work:
            return (
                self.unit_of_work.financial_proofs
                .list_evidence_links_by_evidence(evidence_id)
            )

    def list_evaluation_history(
        self,
        proof_id: UUID,
    ) -> list[ProofEvaluationHistory]:
        """Return persisted evaluation history for a proof."""
        return self.unit_of_work.financial_proofs.list_evaluation_history(
            proof_id
        )

    def get_proof(
        self,
        proof_id: UUID,
    ) -> FinancialProof | None:
        """Retrieve a proof through the repository boundary."""
        return self.unit_of_work.financial_proofs.get_proof(proof_id)

    def list_proofs(
        self,
        subject: str,
    ) -> list[FinancialProof]:
        """Retrieve all financial proofs belonging to a subject."""
        return self.unit_of_work.financial_proofs.list_proofs(subject)

    def get_claim(
        self,
        claim_id: UUID,
    ) -> FinancialClaim | None:
        """Retrieve a claim through the repository boundary."""
        return self.unit_of_work.financial_proofs.get_claim(claim_id)

    def list_claims(
        self,
        subject: str,
    ) -> list[FinancialClaim]:
        """Retrieve standalone claims matching a subject."""
        return self.unit_of_work.financial_proofs.list_claims(subject)

    def list_proof_claims(
        self,
        proof_id: UUID,
    ) -> list[FinancialClaim]:
        """Retrieve claims belonging to a specific proof."""
        return self.unit_of_work.financial_proofs.list_claims_by_proof(
            proof_id
        )

    def add_claims(
        self,
        proof_id: UUID,
        claims: list[FinancialClaim],
    ) -> FinancialProof:
        """Add claims to an existing financial proof atomically."""
        with self.unit_of_work:
            proof = self.unit_of_work.financial_proofs.get_proof(proof_id)

            if proof is None:
                raise NotFoundError(
                    f"Financial proof {proof_id} was not found."
                )

            for claim in claims:
                self.unit_of_work.financial_proofs.add_claim(
                    claim,
                    proof_id,
                )

            self.unit_of_work.flush()

            return proof

    def add_evidence(
        self,
        evidence: Evidence,
    ) -> Evidence:
        """Persist evidence atomically."""
        with self.unit_of_work:
            self.unit_of_work.financial_proofs.add_evidence(evidence)

        return evidence

    def get_evidence(
        self,
        evidence_id: UUID,
    ) -> Evidence | None:
        """Retrieve evidence through the repository boundary."""
        return self.unit_of_work.financial_proofs.get_evidence(evidence_id)

    def add_evidence_link(
        self,
        link: EvidenceLink,
    ) -> EvidenceLink:
        """Persist an evidence link atomically."""
        with self.unit_of_work:
            self.unit_of_work.financial_proofs.add_evidence_link(link)

        return link

    def get_evidence_link(
        self,
        link_id: UUID,
    ) -> EvidenceLink | None:
        """Retrieve an evidence link through the repository boundary."""
        return self.unit_of_work.financial_proofs.get_evidence_link(link_id)

    def list_evidence_links(
        self,
        claim_id: UUID,
    ) -> list[EvidenceLink]:
        """Retrieve evidence links belonging to a claim."""
        return self.unit_of_work.financial_proofs.list_evidence_links_by_claim(
            claim_id
        )

    def attach_evidence_to_claim(
        self,
        claim_id: UUID,
        evidence_id: UUID,
        link: EvidenceLink,
    ) -> EvidenceLink:
        """Attach existing evidence to an existing claim atomically."""
        with self.unit_of_work:
            claim = self.unit_of_work.financial_proofs.get_claim(claim_id)

            if claim is None:
                raise NotFoundError(
                    f"Financial claim {claim_id} was not found."
                )

            evidence = self.unit_of_work.financial_proofs.get_evidence(
                evidence_id
            )

            if evidence is None:
                raise NotFoundError(
                    f"Evidence {evidence_id} was not found."
                )

            if link.claim_id != claim_id:
                raise ValueError(
                    "Evidence link claim_id does not match claim_id."
                )

            if link.evidence_id != evidence_id:
                raise ValueError(
                    "Evidence link evidence_id does not match evidence_id."
                )

            existing_links = (
                self.unit_of_work.financial_proofs
                .list_evidence_links_by_claim(claim_id)
            )

            if any(
                existing.evidence_id == evidence_id
                for existing in existing_links
            ):
                raise ValueError(
                    "Evidence is already linked to this claim."
                )

            self.unit_of_work.financial_proofs.add_evidence_link(link)

        return link




