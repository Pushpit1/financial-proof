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
    """Derive deterministic monetary exposure from contract evaluation failures."""

    @staticmethod
    def analyze(
        contract: FinancialContract,
        evaluation: ContractEvaluationResult,
        context: Mapping[str, Any] | None = None,
    ) -> FinancialBlastRadius:
        values = context or {}
        exposures: list[FinancialExposure] = []

        failed_fields = {
            violation.field
            for violation in evaluation.violations
            if (
                violation.reason_code == "financial_constraint_failed"
                and violation.field is not None
            )
        }

        for constraint in contract.financial_constraints:
            if constraint.field not in failed_fields:
                continue

            actual = values.get(constraint.field)

            if actual is None:
                continue

            amount = Decimal(str(actual))

            if amount < Decimal("0"):
                amount = abs(amount)

            currency = constraint.currency or "UNK"

            if currency == "UNK":
                raise ValueError(
                    "Financial exposure requires a currency for "
                    f"field '{constraint.field}'."
                )

            exposures.append(
                FinancialExposure(
                    field=constraint.field,
                    amount=amount,
                    currency=currency,
                    source_violation_id=next(
                        violation.id
                        for violation in evaluation.violations
                        if (
                            violation.reason_code
                            == "financial_constraint_failed"
                            and violation.field == constraint.field
                        )
                    ),
                )
            )

        return FinancialBlastRadius.from_exposures(
            evaluation.contract_id,
            tuple(exposures),
        )
