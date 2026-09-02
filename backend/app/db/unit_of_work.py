from sqlalchemy.orm import Session

from app.application.ports.unit_of_work import FinancialUnitOfWorkPort
from app.db.repositories.financial_contract import (
    FinancialContractRepository,
)
from app.db.repositories.financial_contract_decision import (
    SqlAlchemyFinancialContractDecisionRepository,
)
from app.db.repositories.financial_proof import (
    SqlAlchemyFinancialProofRepository,
)


class FinancialUnitOfWork(FinancialUnitOfWorkPort):
    """Coordinate financial repositories within one database transaction."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.financial_proofs = SqlAlchemyFinancialProofRepository(session)
        self.contracts = FinancialContractRepository(session)
        self.decisions = SqlAlchemyFinancialContractDecisionRepository(
            session
        )

    def flush(self) -> None:
        """Flush pending changes without committing the transaction."""
        self.session.flush()

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
        """Commit on success and roll back on every failure."""
        if exc_type is not None:
            self.rollback()
            return

        try:
            self.commit()
        except BaseException:
            self.rollback()
            raise
