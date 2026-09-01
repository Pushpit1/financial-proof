from uuid import uuid4

from app.application.ai_investigation.contracts import (
    InvestigationTool,
    InvestigationToolRequest,
    ToolExecutionStatus,
)
from app.application.ai_investigation.inspect_execution import (
    InspectExecutionTool,
)
from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)


def _simulation() -> PaymentSimulation:
    order_id = uuid4()

    payment = Payment(
        order_id=order_id,
        amount_minor=10000,
        currency="INR",
    )

    order = PaymentOrder(
        amount_minor=10000,
        currency="INR",
    )

    event = SimulationEvent(
        sequence=0,
        event=PaymentEvent.AUTHORIZE,
        occurred_at=payment.created_at,
    )

    return PaymentSimulation(
        seed=42,
        initial_payment=payment,
        initial_order=order,
        events=(event,),
    )


def test_inspect_execution_returns_bounded_simulation_data() -> None:
    simulation = _simulation()

    tool = InspectExecutionTool(
        {str(simulation.id): simulation},
    )

    result = tool(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_EXECUTION,
            target_id=simulation.id,
        ),
    )

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.data["id"] == str(simulation.id)
    assert result.data["seed"] == 42
    assert result.data["initial_payment"]
    assert result.data["initial_order"]
    assert len(result.data["events"]) == 1
    assert result.data["events"][0]["sequence"] == 0
    assert result.data["events"][0]["event"] == PaymentEvent.AUTHORIZE.value


def test_inspect_execution_returns_not_found() -> None:
    target_id = uuid4()

    tool = InspectExecutionTool({})

    result = tool(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_EXECUTION,
            target_id=target_id,
        ),
    )

    assert result.status is ToolExecutionStatus.NOT_FOUND
    assert result.data == {}


def test_inspect_execution_is_deterministic() -> None:
    simulation = _simulation()

    tool = InspectExecutionTool(
        {str(simulation.id): simulation},
    )

    first = tool(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_EXECUTION,
            target_id=simulation.id,
        ),
    )

    second = tool(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_EXECUTION,
            target_id=simulation.id,
        ),
    )

    assert first.data == second.data
    assert first.explanation == second.explanation


def test_inspect_execution_does_not_infer_unstored_facts() -> None:
    simulation = _simulation()

    tool = InspectExecutionTool(
        {str(simulation.id): simulation},
    )

    result = tool(
        InvestigationToolRequest(
            tool=InvestigationTool.INSPECT_EXECUTION,
            target_id=simulation.id,
        ),
    )

    assert "root_cause" not in result.data
    assert "financial_impact" not in result.data
    assert "inferred" not in result.data
