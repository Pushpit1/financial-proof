"""Deterministic payment execution inspection tool."""

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    InvestigationToolResult,
    ToolExecutionStatus,
)
from app.domain.models.payment_simulation import PaymentSimulation


class InspectExecutionTool:
    """Expose a bounded, deterministic view of a payment simulation."""

    def __init__(
        self,
        simulations: dict[str, PaymentSimulation],
    ) -> None:
        self._simulations = dict(simulations)

    def __call__(
        self,
        request: InvestigationToolRequest,
    ) -> InvestigationToolResult:
        simulation = self._simulations.get(str(request.target_id))

        if simulation is None:
            return InvestigationToolResult(
                investigation_id=request.investigation_id,
                tool=InvestigationTool.INSPECT_EXECUTION,
                target_id=request.target_id,
                status=ToolExecutionStatus.NOT_FOUND,
                data={},
                explanation="Payment simulation execution was not found.",
            )

        return InvestigationToolResult(
            investigation_id=request.investigation_id,
            tool=InvestigationTool.INSPECT_EXECUTION,
            target_id=request.target_id,
            status=ToolExecutionStatus.SUCCESS,
            data=self._serialize_simulation(simulation),
            explanation=(
                "Execution inspection returned only deterministic simulation "
                "definition data. No inferred cause, financial impact, or "
                "unstated execution facts are included."
            ),
        )

    @classmethod
    def _serialize_simulation(
        cls,
        simulation: PaymentSimulation,
    ) -> dict[str, Any]:
        return {
            "id": str(simulation.id),
            "seed": simulation.seed,
            "initial_payment": cls._serialize_value(
                simulation.initial_payment,
            ),
            "initial_order": cls._serialize_value(
                simulation.initial_order,
            ),
            "events": [
                cls._serialize_value(event)
                for event in simulation.events
            ],
        }

    @classmethod
    def _serialize_value(cls, value: Any) -> Any:
        if isinstance(value, UUID):
            return str(value)

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, date):
            return value.isoformat()

        if isinstance(value, Enum):
            return value.value

        if is_dataclass(value):
            return {
                field.name: cls._serialize_value(
                    getattr(value, field.name),
                )
                for field in fields(value)
            }

        if isinstance(value, tuple):
            return [cls._serialize_value(item) for item in value]

        if isinstance(value, list):
            return [cls._serialize_value(item) for item in value]

        if isinstance(value, dict):
            return {
                str(key): cls._serialize_value(item)
                for key, item in value.items()
            }

        return value
