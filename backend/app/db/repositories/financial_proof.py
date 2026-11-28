"""SQLAlchemy adapter for financial proof persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports.financial_proof import (
    FinancialProofRepositoryPort,
)
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
from app.db.models.financial import (
    EvidenceLinkModel,
    EvidenceModel,
    FinancialClaimModel,
    FinancialProofModel,
    ProofEvaluationModel,
)
from app.domain.models.financial import (
    Evidence,
    EvidenceLink,
    FinancialClaim,
    FinancialProof,
    ProofEvaluationHistory,
)


class SqlAlchemyFinancialProofRepository(
    FinancialProofRepositoryPort
):
    """SQLAlchemy implementation of the financial proof repository port."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_proof(self, proof: FinancialProof) -> None:
        """Persist a financial proof."""
        self.session.add(proof_to_model(proof))
        self.session.flush()

    def update_proof(self, proof: FinancialProof) -> None:
        """Update an existing financial proof."""
        model = self.session.get(FinancialProofModel, proof.id)

        if model is None:
            raise ValueError(
                f"Financial proof {proof.id} was not found."
            )

        updated_model = proof_to_model(proof)

        model.status = updated_model.status
        model.overall_confidence = updated_model.overall_confidence
        model.evaluation_reasons = updated_model.evaluation_reasons
    def get_proof(
        self,
        proof_id: UUID,
    ) -> FinancialProof | None:
        """Retrieve a financial proof."""
        model = self.session.get(FinancialProofModel, proof_id)

        if model is None:
            return None

        return proof_to_domain(model)

    def list_proofs(
        self,
        subject: str,
    ) -> list[FinancialProof]:
        """List proofs for a subject."""
        statement = (
            select(FinancialProofModel)
            .where(FinancialProofModel.subject == subject)
            .order_by(FinancialProofModel.id.asc())
        )

        return [
            proof_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]

    def list_subject_summaries(self) -> list[dict[str, object]]:
        """Aggregate persisted financial proof subjects with counts and latest status."""
        statement = select(FinancialProofModel).order_by(
            FinancialProofModel.subject.asc(),
            FinancialProofModel.id.asc(),
        )
        by_subject: dict[str, dict[str, object]] = {}
        for model in self.session.scalars(statement).all():
            bucket = by_subject.get(model.subject)
            status_val = model.status.value if hasattr(model.status, "value") else str(model.status)
            if bucket is None:
                by_subject[model.subject] = {
                    "subject": model.subject,
                    "proof_count": 1,
                    "ready_count": 1 if status_val == "ready" else 0,
                    "latest_status": status_val,
                    "latest_confidence": model.overall_confidence,
                }
            else:
                bucket["proof_count"] = int(bucket["proof_count"]) + 1  # type: ignore[arg-type]
                if status_val == "ready":
                    bucket["ready_count"] = int(bucket["ready_count"]) + 1  # type: ignore[arg-type]
                bucket["latest_status"] = status_val
                bucket["latest_confidence"] = model.overall_confidence
        return list(by_subject.values())

    def add_claim(
        self,
        claim: FinancialClaim,
        proof_id: UUID | None = None,
    ) -> None:
        """Persist a financial claim."""
        self.session.add(claim_to_model(claim, proof_id))
        self.session.flush()

    def get_claim(
        self,
        claim_id: UUID,
    ) -> FinancialClaim | None:
        """Retrieve a financial claim."""
        model = self.session.get(FinancialClaimModel, claim_id)

        if model is None:
            return None

        return claim_to_domain(model)

    def list_claims(
        self,
        subject: str,
    ) -> list[FinancialClaim]:
        """List claims for a subject."""
        statement = select(FinancialClaimModel).where(
            FinancialClaimModel.subject == subject
        )

        return [
            claim_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]

    def list_claims_by_proof(
        self,
        proof_id: UUID,
    ) -> list[FinancialClaim]:
        """List claims belonging to a proof."""
        statement = (
            select(FinancialClaimModel)
            .where(FinancialClaimModel.proof_id == proof_id)
            .order_by(FinancialClaimModel.id.asc())
        )

        return [
            claim_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]

    def add_evidence(
        self,
        evidence: Evidence,
        proof_id: UUID | None = None,
    ) -> None:
        """Persist evidence."""
        self.session.add(evidence_to_model(evidence, proof_id))
        self.session.flush()

    def get_evidence(
        self,
        evidence_id: UUID,
    ) -> Evidence | None:
        """Retrieve evidence."""
        model = self.session.get(EvidenceModel, evidence_id)

        if model is None:
            return None

        return evidence_to_domain(model)

    def list_evidence_by_proof(
        self,
        proof_id: UUID,
    ) -> list[Evidence]:
        """List evidence belonging to a proof."""
        statement = (
            select(EvidenceModel)
            .where(EvidenceModel.proof_id == proof_id)
            .order_by(EvidenceModel.id.asc())
        )

        return [
            evidence_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]

    def add_evidence_link(
        self,
        link: EvidenceLink,
    ) -> None:
        """Persist an evidence link."""
        self.session.add(evidence_link_to_model(link))
        self.session.flush()

    def get_evidence_link(
        self,
        link_id: UUID,
    ) -> EvidenceLink | None:
        """Retrieve an evidence link."""
        model = self.session.get(EvidenceLinkModel, link_id)

        if model is None:
            return None

        return evidence_link_to_domain(model)

    def list_evidence_links_by_claim(
        self,
        claim_id: UUID,
    ) -> list[EvidenceLink]:
        """List evidence links for a claim."""
        statement = (
            select(EvidenceLinkModel)
            .where(EvidenceLinkModel.claim_id == claim_id)
            .order_by(
                EvidenceLinkModel.created_at.asc(),
                EvidenceLinkModel.id.asc(),
            )
        )

        return [
            evidence_link_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]

    def list_evidence_links_by_evidence(
        self,
        evidence_id: UUID,
    ) -> list[EvidenceLink]:
        """List evidence links for evidence."""
        statement = (
            select(EvidenceLinkModel)
            .where(EvidenceLinkModel.evidence_id == evidence_id)
            .order_by(
                EvidenceLinkModel.created_at.asc(),
                EvidenceLinkModel.id.asc(),
            )
        )

        return [
            evidence_link_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]

    def add_evaluation(
        self,
        evaluation: ProofEvaluationHistory,
    ) -> None:
        """Persist an evaluation history record."""
        self.session.add(proof_evaluation_to_model(evaluation))
        self.session.flush()

    def list_evaluation_history(
        self,
        proof_id: UUID,
    ) -> list[ProofEvaluationHistory]:
        """List evaluation history for a proof."""
        statement = (
            select(ProofEvaluationModel)
            .where(ProofEvaluationModel.proof_id == proof_id)
            .order_by(
                ProofEvaluationModel.evaluated_at.asc(),
                ProofEvaluationModel.id.asc(),
            )
        )

        return [
            proof_evaluation_to_domain(model)
            for model in self.session.scalars(statement).all()
        ]

