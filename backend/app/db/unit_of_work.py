"""Unit of Work for transactional financial persistence."""

from sqlalchemy.orm import Session

from app.db.repositories.financial import (
    EvidenceLinkRepository,
    EvidenceRepository,
    FinancialClaimRepository,
    FinancialProofRepository,
)


class FinancialUnitOfWork:
    """Coordinate financial repositories within one database transaction."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.evidence = EvidenceRepository(session)
        self.claims = FinancialClaimRepository(session)
        self.evidence_links = EvidenceLinkRepository(session)
        self.proofs = FinancialProofRepository(session)

    def commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()

    def rollback(self) -> None:
        """Roll back the current transaction."""
        self.session.rollback()

    def __enter__(self) -> "FinancialUnitOfWork":
        """Enter the unit-of-work context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Commit on success and roll back on failure."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
