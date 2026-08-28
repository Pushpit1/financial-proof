"""Repositories for financial persistence models."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.financial import (
    EvidenceLinkModel,
    EvidenceModel,
    FinancialClaimModel,
    FinancialProofModel,
)


class EvidenceRepository:
    """Repository for evidence persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, evidence: EvidenceModel) -> EvidenceModel:
        """Persist an evidence record."""
        self.session.add(evidence)
        self.session.flush()
        return evidence

    def get_by_id(self, evidence_id: UUID) -> EvidenceModel | None:
        """Return evidence by ID."""
        return self.session.get(EvidenceModel, evidence_id)

    def list_by_proof(self, proof_id: UUID) -> list[EvidenceModel]:
        """Return evidence belonging to a proof."""
        statement = select(EvidenceModel).where(
            EvidenceModel.proof_id == proof_id
        )
        return list(self.session.scalars(statement).all())


class FinancialClaimRepository:
    """Repository for financial claim persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, claim: FinancialClaimModel) -> FinancialClaimModel:
        """Persist a financial claim."""
        self.session.add(claim)
        self.session.flush()
        return claim

    def get_by_id(self, claim_id: UUID) -> FinancialClaimModel | None:
        """Return a financial claim by ID."""
        return self.session.get(FinancialClaimModel, claim_id)

    def list_by_subject(self, subject: str) -> list[FinancialClaimModel]:
        """Return claims belonging to a subject."""
        statement = select(FinancialClaimModel).where(
            FinancialClaimModel.subject == subject
        )
        return list(self.session.scalars(statement).all())

    def list_by_proof(
        self,
        proof_id: UUID,
    ) -> list[FinancialClaimModel]:
        """Return claims belonging to a proof."""
        statement = select(FinancialClaimModel).where(
            FinancialClaimModel.proof_id == proof_id
        )
        return list(self.session.scalars(statement).all())


class EvidenceLinkRepository:
    """Repository for claim/evidence relationships."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, link: EvidenceLinkModel) -> EvidenceLinkModel:
        """Persist an evidence link."""
        self.session.add(link)
        self.session.flush()
        return link

    def get_by_id(self, link_id: UUID) -> EvidenceLinkModel | None:
        """Return an evidence link by ID."""
        return self.session.get(EvidenceLinkModel, link_id)

    def list_by_claim(self, claim_id: UUID) -> list[EvidenceLinkModel]:
        """Return evidence links for a claim."""
        statement = select(EvidenceLinkModel).where(
            EvidenceLinkModel.claim_id == claim_id
        )
        return list(self.session.scalars(statement).all())


class FinancialProofRepository:
    """Repository for financial proof persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, proof: FinancialProofModel) -> FinancialProofModel:
        """Persist a financial proof."""
        self.session.add(proof)
        self.session.flush()
        return proof

    def get_by_id(self, proof_id: UUID) -> FinancialProofModel | None:
        """Return a financial proof by ID."""
        return self.session.get(FinancialProofModel, proof_id)

    def list_by_subject(self, subject: str) -> list[FinancialProofModel]:
        """Return proofs belonging to a subject."""
        statement = select(FinancialProofModel).where(
            FinancialProofModel.subject == subject
        )
        return list(self.session.scalars(statement).all())
