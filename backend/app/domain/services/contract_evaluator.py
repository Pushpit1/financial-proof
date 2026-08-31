from collections.abc import Mapping
from typing import Any

from app.domain.enums.financial import ContractOperator
from app.domain.models.financial import FinancialContract
from app.domain.services.contract_evaluation import (
    ContractEvaluationResult,
    ContractViolation,
)
from app.domain.services.contract_validator import ContractValidator
from app.domain.value_objects.financial import ContractCondition


class ContractEvaluator:
    """Deterministically evaluates financial contract conditions."""

    def __init__(
        self,
        validator: ContractValidator | None = None,
    ) -> None:
        self._validator = validator or ContractValidator()

    def evaluate(
        self,
        contract: FinancialContract,
        context: Mapping[str, Any] | None = None,
    ) -> ContractEvaluationResult:
        validation = self._validator.validate(contract)

        violations: list[ContractViolation] = [
            ContractViolation(
                rule="contract_validation",
                message=error,
            )
            for error in validation.errors
        ]

        if validation.valid:
            values = context or {}

            for rule in (
                *contract.preconditions,
                *contract.invariants,
                *contract.postconditions,
            ):
                if not self._evaluate_condition(
                    rule.condition,
                    values,
                ):
                    violations.append(
                        ContractViolation(
                            rule=rule.name,
                            message=(
                                "Contract condition was not satisfied."
                            ),
                            field=rule.condition.field,
                        )
                    )

        return ContractEvaluationResult(
            contract_id=contract.id,
            passed=not violations,
            violations=tuple(violations),
        )

    @staticmethod
    def _evaluate_condition(
        condition: ContractCondition,
        context: Mapping[str, Any],
    ) -> bool:
        exists = condition.field in context
        actual = context.get(condition.field)

        if condition.operator == ContractOperator.EXISTS:
            return exists

        if condition.operator == ContractOperator.NOT_EXISTS:
            return not exists

        if not exists:
            return False

        expected = condition.value

        if condition.operator == ContractOperator.EQUALS:
            return actual == expected

        if condition.operator == ContractOperator.NOT_EQUALS:
            return actual != expected

        if condition.operator == ContractOperator.GREATER_THAN:
            return actual > expected

        if condition.operator == ContractOperator.GREATER_THAN_OR_EQUAL:
            return actual >= expected

        if condition.operator == ContractOperator.LESS_THAN:
            return actual < expected

        if condition.operator == ContractOperator.LESS_THAN_OR_EQUAL:
            return actual <= expected

        if condition.operator == ContractOperator.IN:
            return actual in expected

        if condition.operator == ContractOperator.NOT_IN:
            return actual not in expected

        return False
