"""Deterministic contract inspection tool."""

from dataclasses import asdict, is_dataclass
from typing import Any

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)
from app.domain.models.financial import FinancialContract


class InspectContractTool:
    """Expose a bounded, deterministic view of a financial contract."""

    def __init__(self, contracts: dict[str, FinancialContract]) -> None:
        self._contracts = dict(contracts)

    def __call__(
        self,
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        contract = self._contracts.get(str(request.target_id))

        if contract is None:
            return InvestigationToolResult(
                investigation_id=request.investigation_id,
                tool=InvestigationTool.INSPECT_CONTRACT,
                target_id=request.target_id,
                status=ToolExecutionStatus.NOT_FOUND,
                explanation="Financial contract was not found.",
            )

        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=InvestigationTool.INSPECT_CONTRACT,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data=self._serialize_contract(contract),
            explanation=(
                "Contract inspection returned only persisted contract "
                "definition data. No execution or inferred facts are included."
            ),
        )

    @staticmethod
    def _serialize_contract(
        contract: FinancialContract,
    ) -> dict[str, Any]:
        return {
            "id": str(contract.id),
            "name": contract.name,
            "version": contract.version,
            "minimum_confidence": str(contract.minimum_confidence.value),
            "minimum_supported_claim_ratio": str(
                contract.minimum_supported_claim_ratio
            ),
            "required_claim_types": [
                claim_type.value
                for claim_type in contract.required_claim_types
            ],
            "inputs": [
                InspectContractTool._serialize_value(item)
                for item in contract.inputs
            ],
            "outputs": [
                InspectContractTool._serialize_value(item)
                for item in contract.outputs
            ],
            "financial_constraints": [
                InspectContractTool._serialize_value(item)
                for item in contract.financial_constraints
            ],
            "preconditions": [
                InspectContractTool._serialize_value(item)
                for item in contract.preconditions
            ],
            "invariants": [
                InspectContractTool._serialize_value(item)
                for item in contract.invariants
            ],
            "postconditions": [
                InspectContractTool._serialize_value(item)
                for item in contract.postconditions
            ],
            "authorizations": [
                InspectContractTool._serialize_value(item)
                for item in contract.authorizations
            ],
            "temporal_rules": [
                InspectContractTool._serialize_value(item)
                for item in contract.temporal_rules
            ],
            "idempotency_policy": (
                InspectContractTool._serialize_value(
                    contract.idempotency_policy
                )
                if contract.idempotency_policy is not None
                else None
            ),
            "state_transitions": [
                InspectContractTool._serialize_value(item)
                for item in contract.state_transitions
            ],
        }

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)

        if isinstance(value, tuple):
            return [
                InspectContractTool._serialize_value(item)
                for item in value
            ]

        if isinstance(value, list):
            return [
                InspectContractTool._serialize_value(item)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                str(key): InspectContractTool._serialize_value(item)
                for key, item in value.items()
            }

        if hasattr(value, "value"):
            return value.value

        return value
