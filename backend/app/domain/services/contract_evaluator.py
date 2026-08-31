from collections.abc import Mapping
from datetime import datetime
from typing import Any

from app.domain.enums.financial import (
    ContractAuthorizationAction,
    ContractOperator,
    ContractTimeRelation,
)
from app.domain.models.financial import FinancialContract
from app.domain.services.contract_evaluation import (
    ContractEvaluationResult,
    ContractViolation,
)
from app.domain.services.contract_validator import ContractValidator
from app.domain.value_objects.financial import (
    ContractAuthorization,
    ContractCondition,
    ContractTemporalRule,
    FinancialConstraint,
)


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
                reason_code="contract_validation",
            )
            for error in validation.errors
        ]

        if validation.valid:
            values = context or {}

            self._evaluate_conditions(contract, values, violations)
            self._evaluate_financial_constraints(
                contract,
                values,
                violations,
            )
            self._evaluate_authorizations(
                contract,
                values,
                violations,
            )
            self._evaluate_temporal_rules(
                contract,
                values,
                violations,
            )

        return ContractEvaluationResult(
            contract_id=contract.id,
            passed=not violations,
            violations=tuple(violations),
        )

    @staticmethod
    def _evaluate_conditions(
        contract: FinancialContract,
        context: Mapping[str, Any],
        violations: list[ContractViolation],
    ) -> None:
        for rule in (
            *contract.preconditions,
            *contract.invariants,
            *contract.postconditions,
        ):
            if not ContractEvaluator._evaluate_condition(
                rule.condition,
                context,
            ):
                violations.append(
                    ContractViolation(
                        rule=rule.name,
                        message="Contract condition was not satisfied.",
                        field=rule.condition.field,
                        reason_code=f"{rule.rule_type.value}_failed",
                    )
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

    @staticmethod
    def _evaluate_financial_constraints(
        contract: FinancialContract,
        context: Mapping[str, Any],
        violations: list[ContractViolation],
    ) -> None:
        for constraint in contract.financial_constraints:
            if not ContractEvaluator._evaluate_financial_constraint(
                constraint,
                context,
            ):
                violations.append(
                    ContractViolation(
                        rule="financial_constraint",
                        message="Financial constraint was not satisfied.",
                        field=constraint.field,
                        reason_code="financial_constraint_failed",
                    )
                )

    @staticmethod
    def _evaluate_financial_constraint(
        constraint: FinancialConstraint,
        context: Mapping[str, Any],
    ) -> bool:
        if constraint.field not in context:
            return False

        actual = context[constraint.field]
        expected = constraint.value

        if constraint.operator == ContractOperator.GREATER_THAN:
            return actual > expected

        if constraint.operator == ContractOperator.GREATER_THAN_OR_EQUAL:
            return actual >= expected

        if constraint.operator == ContractOperator.LESS_THAN:
            return actual < expected

        if constraint.operator == ContractOperator.LESS_THAN_OR_EQUAL:
            return actual <= expected

        if constraint.operator == ContractOperator.EQUALS:
            return actual == expected

        if constraint.operator == ContractOperator.NOT_EQUALS:
            return actual != expected

        return False

    @staticmethod
    def _evaluate_authorizations(
        contract: FinancialContract,
        context: Mapping[str, Any],
        violations: list[ContractViolation],
    ) -> None:
        actor = context.get("actor")
        action = context.get("action")
        resource = context.get("resource")

        for authorization in contract.authorizations:
            if not ContractEvaluator._authorization_matches(
                authorization,
                actor,
                action,
                resource,
            ):
                violations.append(
                    ContractViolation(
                        rule="authorization",
                        message=(
                            "Authorization requirement was not satisfied."
                        ),
                        field="actor",
                        reason_code="authorization_failed",
                    )
                )

    @staticmethod
    def _authorization_matches(
        authorization: ContractAuthorization,
        actor: Any,
        action: Any,
        resource: Any,
    ) -> bool:
        return (
            actor == authorization.actor
            and ContractEvaluator._action_matches(
                authorization.action,
                action,
            )
            and resource == authorization.resource
        )

    @staticmethod
    def _action_matches(
        expected: ContractAuthorizationAction,
        actual: Any,
    ) -> bool:
        if isinstance(actual, ContractAuthorizationAction):
            return actual == expected

        return actual == expected.value

    @staticmethod
    def _evaluate_temporal_rules(
        contract: FinancialContract,
        context: Mapping[str, Any],
        violations: list[ContractViolation],
    ) -> None:
        for rule in contract.temporal_rules:
            actual = context.get(rule.field)

            if not isinstance(actual, datetime):
                violations.append(
                    ContractViolation(
                        rule="temporal_rule",
                        message=(
                            "Temporal rule requires a datetime "
                            "context value."
                        ),
                        field=rule.field,
                        reason_code="temporal_value_missing",
                    )
                )
                continue

            if not ContractEvaluator._temporal_rule_matches(
                rule,
                actual,
            ):
                violations.append(
                    ContractViolation(
                        rule="temporal_rule",
                        message="Temporal rule was not satisfied.",
                        field=rule.field,
                        reason_code="temporal_rule_failed",
                    )
                )

    @staticmethod
    def _temporal_rule_matches(
        rule: ContractTemporalRule,
        actual: datetime,
    ) -> bool:
        if rule.relation == ContractTimeRelation.BEFORE:
            return actual < rule.start

        if rule.relation == ContractTimeRelation.AFTER:
            return actual > rule.start

        if rule.relation == ContractTimeRelation.ON_OR_BEFORE:
            return actual <= rule.start

        if rule.relation == ContractTimeRelation.ON_OR_AFTER:
            return actual >= rule.start

        if rule.relation == ContractTimeRelation.BETWEEN:
            return (
                rule.end is not None
                and rule.start <= actual <= rule.end
            )

        return False
