from dataclasses import dataclass

from app.domain.models.financial import FinancialContract


@dataclass(frozen=True)
class ContractValidationResult:
    """Deterministic result of validating a financial contract."""

    valid: bool
    errors: tuple[str, ...] = ()


class ContractValidator:
    """Validates the structural integrity of financial contracts."""

    def validate(
        self,
        contract: FinancialContract,
    ) -> ContractValidationResult:
        errors: list[str] = []

        self._validate_identity(contract, errors)
        self._validate_required_claim_types(contract, errors)
        self._validate_rules(contract, errors)
        self._validate_inputs_and_outputs(contract, errors)
        self._validate_authorizations(contract, errors)
        self._validate_temporal_rules(contract, errors)
        self._validate_idempotency(contract, errors)
        self._validate_state_transitions(contract, errors)

        return ContractValidationResult(
            valid=not errors,
            errors=tuple(errors),
        )

    @staticmethod
    def _validate_identity(
        contract: FinancialContract,
        errors: list[str],
    ) -> None:
        if not contract.name.strip():
            errors.append("Contract name cannot be empty.")

        if contract.version < 1:
            errors.append(
                "Contract version must be at least 1."
            )

    @staticmethod
    def _validate_required_claim_types(
        contract: FinancialContract,
        errors: list[str],
    ) -> None:
        seen = set()

        for claim_type in contract.required_claim_types:
            if claim_type in seen:
                errors.append(
                    "Duplicate required claim type: "
                    f"'{claim_type.value}'."
                )

            seen.add(claim_type)

    @staticmethod
    def _validate_rules(
        contract: FinancialContract,
        errors: list[str],
    ) -> None:
        for rule in (
            *contract.preconditions,
            *contract.invariants,
            *contract.postconditions,
        ):
            if not rule.name.strip():
                errors.append(
                    "Contract rule name cannot be empty."
                )

            if not rule.condition.field.strip():
                errors.append(
                    "Contract rule condition field cannot be empty."
                )

    @staticmethod
    def _validate_inputs_and_outputs(
        contract: FinancialContract,
        errors: list[str],
    ) -> None:
        input_names = {
            field.name for field in contract.inputs
        }
        output_names = {
            field.name for field in contract.outputs
        }

        overlap = input_names & output_names

        for name in sorted(overlap):
            errors.append(
                f"Contract field cannot be both input and output: "
                f"'{name}'."
            )

    @staticmethod
    def _validate_authorizations(
        contract: FinancialContract,
        errors: list[str],
    ) -> None:
        seen: set[tuple[str, str, str]] = set()

        for authorization in contract.authorizations:
            key = (
                authorization.actor,
                authorization.action.value,
                authorization.resource,
            )

            if key in seen:
                errors.append(
                    "Duplicate contract authorization."
                )

            seen.add(key)

    @staticmethod
    def _validate_temporal_rules(
        contract: FinancialContract,
        errors: list[str],
    ) -> None:
        seen: set[tuple[str, str, object, object]] = set()

        for rule in contract.temporal_rules:
            key = (
                rule.field,
                rule.relation.value,
                rule.start,
                rule.end,
            )

            if key in seen:
                errors.append(
                    "Duplicate contract temporal rule."
                )

            seen.add(key)

    @staticmethod
    def _validate_idempotency(
        contract: FinancialContract,
        errors: list[str],
    ) -> None:
        policy = contract.idempotency_policy

        if policy is None:
            return

        if policy.mode.value != "disabled":
            input_names = {
                field.name for field in contract.inputs
            }

            if (
                input_names
                and policy.key_field not in input_names
            ):
                errors.append(
                    "Idempotency key field must reference a "
                    "declared contract input field."
                )

    @staticmethod
    def _validate_state_transitions(
        contract: FinancialContract,
        errors: list[str],
    ) -> None:
        seen: set[tuple[str, str, str]] = set()

        for transition in contract.state_transitions:
            key = (
                transition.from_state.value,
                transition.to_state.value,
                transition.trigger.value,
            )

            if key in seen:
                errors.append(
                    "Duplicate contract state transition."
                )

            seen.add(key)
