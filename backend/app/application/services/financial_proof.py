"""Application services for financial proof workflows."""

from uuid import UUID

from app.application.dto.financial_proof import FinancialProofAggregate
from app.core.errors.domain import NotFoundError
from app.db.mappers.financial import (
    claim_to_domain,
    claim_to_model,
    evidence_link_to_domain,
    evidence_link_to_model,
    evidence_to_domain,
    evidence_to_model,
    proof_evaluation_to_domain,
    proof_evaluation_to_model,
    proof_to_domain,
    proof_to_model,
)
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
            self.unit_of_work.proofs.add(proof_to_model(proof))

            for claim in claims:
                self.unit_of_work.claims.add(
                    claim_to_model(claim, proof.id)
                )

            for item in evidence:
                self.unit_of_work.evidence.add(
                    evidence_to_model(item, proof.id)
                )

            for link in evidence_links:
                if link.claim_id not in {claim.id for claim in claims}:
                    raise ValueError(
                        "Evidence link references a claim "
                        "outside this proof."
                    )

                if link.evidence_id not in {
                    item.id for item in evidence
                }:
                    raise ValueError(
                        "Evidence link references evidence "
                        "outside this proof."
                    )

                self.unit_of_work.evidence_links.add(
                    evidence_link_to_model(link)
                )

        return proof

    def get_proof_aggregate(
        self,
        proof_id: UUID,
    ) -> FinancialProofAggregate | None:
        """Retrieve a complete financial proof aggregate."""
        proof_model = self.unit_of_work.proofs.get_by_id(proof_id)

        if proof_model is None:
            return None

        claim_models = self.unit_of_work.claims.list_by_proof(proof_id)

        claim_ids = {claim.id for claim in claim_models}

        evidence_link_models = []

        for claim_id in claim_ids:
            evidence_link_models.extend(
                self.unit_of_work.evidence_links.list_by_claim(
                    claim_id
                )
            )

        evidence_models = self.unit_of_work.evidence.list_by_proof(
            proof_id
        )

        return FinancialProofAggregate(
            proof=proof_to_domain(proof_model),
            claims=tuple(
                claim_to_domain(model)
                for model in claim_models
            ),
            evidence=tuple(
                evidence_to_domain(model)
                for model in evidence_models
            ),
            evidence_links=tuple(
                evidence_link_to_domain(model)
                for model in evidence_link_models
            ),
        )

    def evaluate_proof(
        self,
        proof_id: UUID,
    ) -> FinancialProof | None:
        """Evaluate a proof and persist both current state and history."""
        with self.unit_of_work:
            proof_model = self.unit_of_work.proofs.get_by_id(proof_id)

            if proof_model is None:
                return None

            claim_models = self.unit_of_work.claims.list_by_proof(
                proof_id
            )

            claims = [
                claim_to_domain(model)
                for model in claim_models
            ]

            proof = proof_to_domain(proof_model)

            evaluation = self.evaluator.evaluate(claims)

            proof.apply_evaluation(evaluation)

            updated_model = proof_to_model(proof)

            proof_model.status = updated_model.status
            proof_model.overall_confidence = (
                updated_model.overall_confidence
            )
            proof_model.evaluation_reasons = (
                updated_model.evaluation_reasons
            )

            self.unit_of_work.evaluations.add(
                proof_evaluation_to_model(
                    evaluation,
                    proof_id,
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
            models = self.unit_of_work.evidence_links.list_by_evidence(
                evidence_id
            )

        return [evidence_link_to_domain(model) for model in models]

    def list_evaluation_history(
        self,
        proof_id: UUID,
    ) -> list[ProofEvaluationHistory]:
        """Return persisted evaluation history for a proof."""
        models = self.unit_of_work.evaluations.list_by_proof(proof_id)

        return [
            proof_evaluation_to_domain(model)
            for model in models
        ]

    def get_proof(self, proof_id: UUID) -> FinancialProof | None:
        """Retrieve a proof through the repository boundary."""
        model = self.unit_of_work.proofs.get_by_id(proof_id)

        if model is None:
            return None

        return proof_to_domain(model)

    def list_proofs(self, subject: str) -> list[FinancialProof]:
        """Retrieve all financial proofs belonging to a subject."""
        models = self.unit_of_work.proofs.list_by_subject(subject)

        return [proof_to_domain(model) for model in models]

    def get_claim(self, claim_id: UUID) -> FinancialClaim | None:
        """Retrieve a claim through the repository boundary."""
        model = self.unit_of_work.claims.get_by_id(claim_id)

        if model is None:
            return None

        return claim_to_domain(model)

    def list_claims(self, subject: str) -> list[FinancialClaim]:
        """Retrieve standalone claims matching a subject."""
        models = self.unit_of_work.claims.list_by_subject(subject)

        return [claim_to_domain(model) for model in models]

    def list_proof_claims(
        self,
        proof_id: UUID,
    ) -> list[FinancialClaim]:
        """Retrieve claims belonging to a specific proof."""
        models = self.unit_of_work.claims.list_by_proof(proof_id)

        return [claim_to_domain(model) for model in models]

    def add_claims(
        self,
        proof_id: UUID,
        claims: list[FinancialClaim],
    ) -> FinancialProof:
        """Add claims to an existing financial proof atomically."""
        with self.unit_of_work:
            proof_model = self.unit_of_work.proofs.get_by_id(proof_id)

            if proof_model is None:
                raise NotFoundError(
                    f"Financial proof {proof_id} was not found."
                )

            for claim in claims:
                self.unit_of_work.claims.add(
                    claim_to_model(claim, proof_id)
                )

            return proof_to_domain(proof_model)

    def add_evidence(self, evidence: Evidence) -> Evidence:
        """Persist evidence atomically."""
        with self.unit_of_work:
            self.unit_of_work.evidence.add(
                evidence_to_model(evidence)
            )

        return evidence

    def get_evidence(self, evidence_id: UUID) -> Evidence | None:
        """Retrieve evidence through the repository boundary."""
        model = self.unit_of_work.evidence.get_by_id(evidence_id)

        if model is None:
            return None

        return evidence_to_domain(model)

    def add_evidence_link(self, link: EvidenceLink) -> EvidenceLink:
        """Persist an evidence link atomically."""
        with self.unit_of_work:
            self.unit_of_work.evidence_links.add(
                evidence_link_to_model(link)
            )

        return link

    def get_evidence_link(
        self,
        link_id: UUID,
    ) -> EvidenceLink | None:
        """Retrieve an evidence link through the repository boundary."""
        model = self.unit_of_work.evidence_links.get_by_id(link_id)

        if model is None:
            return None

        return evidence_link_to_domain(model)

    def list_evidence_links(
        self,
        claim_id: UUID,
    ) -> list[EvidenceLink]:
        """Retrieve evidence links belonging to a claim."""
        models = self.unit_of_work.evidence_links.list_by_claim(
            claim_id
        )

        return [evidence_link_to_domain(model) for model in models]

    def attach_evidence_to_claim(
        self,
        claim_id: UUID,
        evidence_id: UUID,
        link: EvidenceLink,
    ) -> EvidenceLink:
        """Attach existing evidence to an existing claim atomically."""
        with self.unit_of_work:
            claim_model = self.unit_of_work.claims.get_by_id(claim_id)

            if claim_model is None:
                raise NotFoundError(
                    f"Financial claim {claim_id} was not found."
                )

            evidence_model = self.unit_of_work.evidence.get_by_id(
                evidence_id
            )

            if evidence_model is None:
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

            existing_links = self.unit_of_work.evidence_links.list_by_claim(
                claim_id
            )

            if any(
                existing.evidence_id == evidence_id
                for existing in existing_links
            ):
                raise ValueError(
                    "Evidence is already linked to this claim."
                )

            self.unit_of_work.evidence_links.add(
                evidence_link_to_model(link)
            )

        return link
