"""Repositories for financial persistence models."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.financial import (
    EvidenceLinkModel,
    EvidenceModel,
    FinancialClaimModel,
    FinancialContractDecisionModel,
    FinancialContractModel,
    FinancialProofModel,
    ProofEvaluationModel,
)


class FinancialProofRepository:
    """Repository for financial proof persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, proof: FinancialProofModel) -> None:
        """Add a financial proof."""
        self.session.add(proof)

    def get_by_id(self, proof_id: UUID) -> FinancialProofModel | None:
        """Get a financial proof by ID."""
        return self.session.get(FinancialProofModel, proof_id)

    def list_by_subject(self, subject: str) -> list[FinancialProofModel]:
        """List financial proofs by subject."""
        statement = (
            select(FinancialProofModel)
            .where(FinancialProofModel.subject == subject)
            .order_by(FinancialProofModel.id.asc())
        )
        return list(self.session.scalars(statement).all())


class FinancialClaimRepository:
    """Repository for financial claim persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, claim: FinancialClaimModel) -> None:
        """Add a financial claim."""
        self.session.add(claim)

    def get_by_id(self, claim_id: UUID) -> FinancialClaimModel | None:
        """Get a financial claim by ID."""
        return self.session.get(FinancialClaimModel, claim_id)

    def list_by_subject(self, subject: str) -> list[FinancialClaimModel]:
        """List claims by subject."""
        statement = select(FinancialClaimModel).where(
            FinancialClaimModel.subject == subject
        )
        return list(self.session.scalars(statement).all())

    def list_by_proof(self, proof_id: UUID) -> list[FinancialClaimModel]:
        """List claims belonging to a proof."""
        statement = (
            select(FinancialClaimModel)
            .where(FinancialClaimModel.proof_id == proof_id)
            .order_by(FinancialClaimModel.id.asc())
        )
        return list(self.session.scalars(statement).all())


class EvidenceRepository:
    """Repository for evidence persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, evidence: EvidenceModel) -> EvidenceModel:
        """Add evidence and return the persisted model instance."""
        self.session.add(evidence)
        return evidence

    def get_by_id(self, evidence_id: UUID) -> EvidenceModel | None:
        """Get evidence by ID."""
        return self.session.get(EvidenceModel, evidence_id)

    def list_by_proof(self, proof_id: UUID) -> list[EvidenceModel]:
        """List evidence belonging to a proof."""
        statement = (
            select(EvidenceModel)
            .where(EvidenceModel.proof_id == proof_id)
            .order_by(EvidenceModel.id.asc())
        )
        return list(self.session.scalars(statement).all())


class EvidenceLinkRepository:
    """Repository for evidence link persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, link: EvidenceLinkModel) -> EvidenceLinkModel:
        """Add an evidence link."""
        self.session.add(link)
        return link

    def get_by_id(self, link_id: UUID) -> EvidenceLinkModel | None:
        """Get an evidence link by ID."""
        return self.session.get(EvidenceLinkModel, link_id)

    def list_by_claim(self, claim_id: UUID) -> list[EvidenceLinkModel]:
        """List evidence links for a claim."""
        statement = (
            select(EvidenceLinkModel)
            .where(EvidenceLinkModel.claim_id == claim_id)
            .order_by(
                EvidenceLinkModel.created_at.asc(),
                EvidenceLinkModel.id.asc(),
            )
        )
        return list(self.session.scalars(statement).all())

    def list_by_evidence(
        self,
        evidence_id: UUID,
    ) -> list[EvidenceLinkModel]:
        """List evidence links for evidence."""
        statement = (
            select(EvidenceLinkModel)
            .where(EvidenceLinkModel.evidence_id == evidence_id)
            .order_by(
                EvidenceLinkModel.created_at.asc(),
                EvidenceLinkModel.id.asc(),
            )
        )
        return list(self.session.scalars(statement).all())


class FinancialContractRepository:
    """Repository for financial contract persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, contract: FinancialContractModel) -> None:
        """Add a financial contract."""
        self.session.add(contract)

    def get_by_id(
        self,
        contract_id: UUID,
    ) -> FinancialContractModel | None:
        """Get a financial contract by ID."""
        return self.session.get(
            FinancialContractModel,
            contract_id,
        )

    def get_by_name_and_version(
        self,
        name: str,
        version: int,
    ) -> FinancialContractModel | None:
        """Get a specific contract version by name."""
        statement = select(FinancialContractModel).where(
            FinancialContractModel.name == name,
            FinancialContractModel.version == version,
        )
        return self.session.scalars(statement).first()

    def list_by_name(
        self,
        name: str,
    ) -> list[FinancialContractModel]:
        """List all versions of a financial contract."""
        statement = (
            select(FinancialContractModel)
            .where(FinancialContractModel.name == name)
            .order_by(FinancialContractModel.version.asc())
        )
        return list(self.session.scalars(statement).all())


class ProofEvaluationRepository:
    """Repository for proof evaluation persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, evaluation: ProofEvaluationModel) -> None:
        """Add a proof evaluation."""
        self.session.add(evaluation)

    def get_by_id(
        self,
        evaluation_id: UUID,
    ) -> ProofEvaluationModel | None:
        """Get a proof evaluation by ID."""
        return self.session.get(
            ProofEvaluationModel,
            evaluation_id,
        )

    def list_by_proof(
        self,
        proof_id: UUID,
    ) -> list[ProofEvaluationModel]:
        """List evaluations for a proof."""
        statement = (
            select(ProofEvaluationModel)
            .where(ProofEvaluationModel.proof_id == proof_id)
            .order_by(
                ProofEvaluationModel.evaluated_at.asc(),
                ProofEvaluationModel.id.asc(),
            )
        )
        return list(self.session.scalars(statement).all())


class FinancialContractDecisionRepository:
    """Repository for financial contract decision persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(
        self,
        decision: FinancialContractDecisionModel,
    ) -> None:
        """Add a contract decision."""
        self.session.add(decision)

    def get_by_id(
        self,
        decision_id: UUID,
    ) -> FinancialContractDecisionModel | None:
        """Get a contract decision by ID."""
        return self.session.get(
            FinancialContractDecisionModel,
            decision_id,
        )

    def list_by_contract(
        self,
        contract_id: UUID,
    ) -> list[FinancialContractDecisionModel]:
        """List decisions for a contract deterministically."""
        statement = (
            select(FinancialContractDecisionModel)
            .where(
                FinancialContractDecisionModel.contract_id
                == contract_id
            )
            .order_by(
                FinancialContractDecisionModel.evaluated_at.asc(),
                FinancialContractDecisionModel.id.asc(),
            )
        )

        return list(self.session.scalars(statement).all())
