"""Bounded deterministic AI investigation API routes."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.dependencies import get_financial_contract_service
from app.api.routes.financial_simulation import _simulations
from app.application.ai_investigation.audit import (
    InMemoryInvestigationAuditSink,
)
from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
)
from app.application.ai_investigation.engine import AIInvestigationEngine
from app.application.ai_investigation.inspect_contract import (
    InspectContractTool,
)
from app.application.ai_investigation.inspect_execution import (
    InspectExecutionTool,
)
from app.application.ai_investigation.registry import InvestigationToolRegistry
from app.application.services.financial_contract import (
    FinancialContractApplicationService,
)

router = APIRouter(prefix="/investigations", tags=["ai-investigation"])


class InvestigationRequest(BaseModel):
    contract_id: UUID | None = None
    simulation_id: UUID | None = None
    violation_summary: str = ""


class InvestigationToolResultOut(BaseModel):
    tool: str
    status: str
    explanation: str
    data: dict[str, object]


class InvestigationResponse(BaseModel):
    investigation_id: UUID
    ai_advisory_only: bool
    overrides_deterministic_verification: bool
    summary: str
    root_cause_hypothesis: str
    recommended_actions: list[str]
    tool_results: list[InvestigationToolResultOut]
    audit_record_count: int


@router.get("/tools")
async def list_investigation_tools() -> dict[str, object]:
    """List bounded deterministic tools available to the investigation engine."""
    return {
        "ai_advisory_only": True,
        "overrides_deterministic_verification": False,
        "tools": [
            {
                "name": InvestigationTool.INSPECT_CONTRACT.value,
                "description": (
                    "Read persisted contract rules and constraints without "
                    "mutating state."
                ),
            },
            {
                "name": InvestigationTool.INSPECT_EXECUTION.value,
                "description": (
                    "Inspect deterministic payment simulation events and initial state."
                ),
            },
        ],
    }


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
)
async def run_investigation(
    request: InvestigationRequest,
    contract_service: FinancialContractApplicationService = Depends(  # noqa: B008
        get_financial_contract_service
    ),
) -> InvestigationResponse:
    """Run bounded deterministic investigation tools and return advisory findings."""
    contracts_map = {}
    if request.contract_id is not None:
        try:
            contract = contract_service.get_contract(request.contract_id)
            if contract is not None:
                contracts_map[str(contract.id)] = contract
        except Exception:
            contracts_map = {}

    simulations_map = {str(k): v for k, v in _simulations.items()}

    registry = InvestigationToolRegistry(
        permissions={
            InvestigationTool.INSPECT_CONTRACT,
            InvestigationTool.INSPECT_EXECUTION,
        }
    )
    registry.register(
        InvestigationTool.INSPECT_CONTRACT,
        InspectContractTool(contracts_map),
    )
    registry.register(
        InvestigationTool.INSPECT_EXECUTION,
        InspectExecutionTool(simulations_map),
    )

    audit_sink = InMemoryInvestigationAuditSink()
    engine = AIInvestigationEngine(registry=registry, audit_sink=audit_sink)
    investigation_id = uuid4()
    results: list[InvestigationToolResultOut] = []

    if request.contract_id is not None:
        res = engine.investigate(
            InvestigationToolRequest(
                investigation_id=investigation_id,
                tool=InvestigationTool.INSPECT_CONTRACT,
                target_id=request.contract_id,
            )
        )
        results.append(
            InvestigationToolResultOut(
                tool=res.tool.value,
                status=res.status.value,
                explanation=res.explanation,
                data=res.data,
            )
        )

    if request.simulation_id is not None:
        res = engine.investigate(
            InvestigationToolRequest(
                investigation_id=investigation_id,
                tool=InvestigationTool.INSPECT_EXECUTION,
                target_id=request.simulation_id,
            )
        )
        results.append(
            InvestigationToolResultOut(
                tool=res.tool.value,
                status=res.status.value,
                explanation=res.explanation,
                data=res.data,
            )
        )

    hypotheses: list[str] = []
    actions: list[str] = []
    text = request.violation_summary.lower()

    if "duplicate" in text or "idempoten" in text:
        hypotheses.append(
            "Duplicate operation sequence executed without a unique idempotency guard."
        )
        actions.append(
            "Enforce idempotency_key uniqueness and replay-safe state transitions before execution."
        )
    if "refund" in text or "exceed" in text or "amount" in text:
        hypotheses.append(
            "Refund or capture amount exceeded the authorized payment ceiling."
        )
        actions.append(
            "Bind Runtime Guardian refund ceiling guard (refund_amount <= payment_amount)."
        )
    if "order" in text or "transition" in text or "state" in text:
        hypotheses.append(
            "Out-of-order or invalid payment state transition reached the state machine."
        )
        actions.append(
            "Reject transitions outside AUTHORIZE -> CAPTURE -> REFUND in webhook and API handlers."
        )

    if not hypotheses:
        hypotheses.append(
            "Bounded inspection completed on available deterministic contract "
            "and execution artifacts."
        )
        actions.append(
            "Verify failed invariants via before/after snapshot comparison "
            "after applying contract fixes."
        )

    return InvestigationResponse(
        investigation_id=investigation_id,
        ai_advisory_only=True,
        overrides_deterministic_verification=False,
        summary=(
            f"Executed {len(results)} bounded inspection tool(s). "
            "Advisory findings do not override deterministic verification."
        ),
        root_cause_hypothesis=" ".join(hypotheses),
        recommended_actions=actions,
        tool_results=results,
        audit_record_count=len(audit_sink.records()),
    )
