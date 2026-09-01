from uuid import UUID

from sqlalchemy.orm import Session

from app.application.ports.financial_blast_radius import (
    FinancialBlastRadiusRepository,
)
from app.domain.models.financial_blast_radius import FinancialBlastRadius


class SqlAlchemyFinancialBlastRadiusRepository(
    FinancialBlastRadiusRepository,
):
    """SQLAlchemy implementation of blast-radius persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        analysis: FinancialBlastRadius,
    ) -> FinancialBlastRadius:
        """Persist a blast-radius analysis."""
        from app.db.mappers.financial_blast_radius import (
            financial_blast_radius_to_model,
        )

        model = financial_blast_radius_to_model(analysis)
        self.session.add(model)
        self.session.flush()

        return analysis

    def get_by_id(
        self,
        analysis_id: UUID,
    ) -> FinancialBlastRadius | None:
        """Retrieve a blast-radius analysis by ID."""
        from app.db.mappers.financial_blast_radius import (
            financial_blast_radius_to_domain,
        )
        from app.db.models.financial_blast_radius import (
            FinancialBlastRadiusModel,
        )

        model = self.session.get(
            FinancialBlastRadiusModel,
            analysis_id,
        )

        if model is None:
            return None

        return financial_blast_radius_to_domain(model)
