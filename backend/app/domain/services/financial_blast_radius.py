from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from app.domain.models.financial import FinancialContract
from app.domain.models.financial_blast_radius import (
    FinancialBlastRadius,
    FinancialExposure,
)
from app.domain.services.contract_evaluation import ContractEvaluationResult


class FinancialBlastRadiusAnalyzer:
    """Analyze contract violations and deterministically calculate exposure."""

    @classmethod
    def analyze(
        cls,
        contract: FinancialContract,
        evaluation: ContractEvaluationResult,
        context: Mapping[str, Any] | None = None,
    ) -> FinancialBlastRadius:
        """Convert failed financial constraints into financial exposures."""

        values = context or {}
        exposures: list[FinancialExposure] = []

        constraints_by_field = {
            constraint.field: constraint
            for constraint in contract.financial_constraints
        }

        for violation in evaluation.violations:
            if violation.reason_code != "financial_constraint_failed":
                continue

            if violation.field is None:
                continue

            constraint = constraints_by_field.get(violation.field)
            if constraint is None:
                continue

            actual = values.get(violation.field)

            if not isinstance(actual, Decimal):
                continue

            currency = constraint.currency
            if currency is None:
                continue

            amount = abs(actual)

            explanation = (
                f"Financial constraint on '{violation.field}' failed; "
                f"direct financial exposure is {amount} {currency}."
            )

            exposures.append(
                FinancialExposure(
                    source_violation_id=violation.id,
                    field=violation.field,
                    amount=amount,
                    currency=currency,
                    explanation=explanation,
                    direct_loss=amount,
                    actual_exposure=amount,
                    maximum_exposure=amount,
                )
            )

        return FinancialBlastRadius(
            exposures=tuple(exposures),
        )
