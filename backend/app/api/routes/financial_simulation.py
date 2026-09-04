"""Financial simulation API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.domain.enums.payment import PaymentEvent
from app.domain.models.adversarial_simulation import (
    DelayedEventAttack,
    DuplicateEventAttack,
    OutOfOrderEventAttack,
)
from app.domain.models.lost_response import LostResponseScenario
from app.domain.models.partial_failure import PartialFailureScenario
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
    SimulationTraceEntry,
)
from app.domain.models.retry import RetryScenario
from app.domain.models.stale_worker_state import StaleWorkerStateAttack
from app.domain.models.worker_crash import WorkerCrashScenario
from app.domain.services.adversarial_scenario_composer import (
    AdversarialScenarioComposer,
)
from app.domain.services.adversarial_scenario_executor import (
    AdversarialScenarioExecutor,
)
from app.domain.services.counterexample_shrinker import CounterexampleShrinker
from app.domain.services.payment_simulation_runner import PaymentSimulationRunner
from app.domain.services.payment_state_machine import InvalidPaymentTransition
from app.schemas.counterexample import CounterexampleEventResponse, CounterexampleResponse
from app.schemas.financial_simulation import (
    AdversarialFailureResponse,
    AdversarialSimulationResponse,
    AttackOutcomeResponse,
    AttackRequest,
    SimulationCreateRequest,
    SimulationEventResponse,
    SimulationResponse,
    SimulationResultResponse,
    SimulationStateResponse,
    SimulationTraceEntryResponse,
)

router = APIRouter(
    prefix="/simulations",
    tags=["financial-simulations"],
)

_simulations: dict[UUID, PaymentSimulation] = {}


def _event_response(event: SimulationEvent) -> SimulationEventResponse:
    return SimulationEventResponse(
        id=event.id,
        sequence=event.sequence,
        event=event.event.value,
        occurred_at=event.occurred_at,
    )


def _trace_entry_response(
    entry: SimulationTraceEntry,
) -> SimulationTraceEntryResponse:
    return SimulationTraceEntryResponse(
        sequence=entry.sequence,
        event=entry.event.value,
        occurred_at=entry.occurred_at,
    )


def _result_response(result) -> SimulationResultResponse:
    return SimulationResultResponse(
        simulation_id=result.simulation_id,
        seed=result.seed,
        final_payment_state=result.final_payment.state.value,
        final_order_state=result.final_order.state.value,
        trace=[_trace_entry_response(entry) for entry in result.trace],
        snapshots=[
            SimulationStateResponse(
                payment_state=snapshot.payment.state.value,
                order_state=snapshot.order.state.value,
            )
            for snapshot in result.snapshots
        ],
    )


def _build_simulation(request: SimulationCreateRequest) -> PaymentSimulation:
    order = PaymentOrder(
        amount_minor=request.amount_minor,
        currency=request.currency.upper(),
    )

    payment = Payment(
        order_id=order.id,
        amount_minor=request.amount_minor,
        currency=request.currency.upper(),
    )

    events = tuple(
        SimulationEvent(
            sequence=sequence,
            event=PaymentEvent(event.event),
            occurred_at=event.occurred_at,
        )
        for sequence, event in enumerate(request.events)
    )

    return PaymentSimulation(
        seed=request.seed,
        initial_payment=payment,
        initial_order=order,
        events=events,
    )


def _build_attack(simulation: PaymentSimulation, request: AttackRequest):
    attack_type = request.attack_type.strip().lower()

    if attack_type == "duplicate":
        return DuplicateEventAttack(
            simulation_id=simulation.id,
            target_sequence=request.target_sequence,
        )

    if attack_type == "out_of_order":
        if request.source_sequence is None:
            raise ValueError(
                "source_sequence is required for out_of_order attacks"
            )
        return OutOfOrderEventAttack(
            simulation_id=simulation.id,
            source_sequence=request.source_sequence,
            target_sequence=request.target_sequence,
        )

    if attack_type == "delayed":
        if request.delay_seconds is None:
            raise ValueError("delay_seconds is required for delayed attacks")
        return DelayedEventAttack(
            simulation_id=simulation.id,
            target_sequence=request.target_sequence,
            delivery_delay_seconds=request.delay_seconds,
        )

    if attack_type == "retry":
        if request.retry_count is None:
            raise ValueError("retry_count is required for retry attacks")
        return RetryScenario(
            simulation_id=simulation.id,
            target_sequence=request.target_sequence,
            retry_count=request.retry_count,
        )

    if attack_type == "partial_failure":
        return PartialFailureScenario(
            simulation_id=simulation.id,
            target_sequence=request.target_sequence,
        )

    if attack_type == "lost_response":
        return LostResponseScenario(
            simulation_id=simulation.id,
            target_sequence=request.target_sequence,
        )

    if attack_type == "worker_crash":
        return WorkerCrashScenario(
            simulation_id=simulation.id,
            target_sequence=request.target_sequence,
        )

    if attack_type == "stale_worker":
        if (
            request.worker_sequence is None
            or request.incoming_sequence is None
        ):
            raise ValueError(
                "worker_sequence and incoming_sequence are required "
                "for stale_worker attacks",
            )
        return StaleWorkerStateAttack(
            simulation_id=simulation.id,
            worker_sequence=request.worker_sequence,
            incoming_sequence=request.incoming_sequence,
        )

    raise ValueError(f"Unsupported attack type: {request.attack_type}")


@router.post(
    "",
    response_model=SimulationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_simulation(
    request: SimulationCreateRequest,
) -> SimulationResponse:
    """Create and execute a deterministic baseline simulation."""
    try:
        simulation = _build_simulation(request)
        result = PaymentSimulationRunner.run(simulation)
    except (IndexError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    _simulations[simulation.id] = simulation

    return SimulationResponse(
        id=simulation.id,
        seed=simulation.seed,
        amount_minor=simulation.initial_payment.amount_minor,
        currency=simulation.initial_payment.currency,
        events=[_event_response(event) for event in simulation.events],
        result=_result_response(result),
    )


@router.get(
    "/{simulation_id}",
    response_model=SimulationResponse,
)
async def get_simulation(simulation_id: UUID) -> SimulationResponse:
    """Return a previously created in-process simulation."""
    simulation = _simulations.get(simulation_id)

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found",
        )

    try:
        result = PaymentSimulationRunner.run(simulation)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return SimulationResponse(
        id=simulation.id,
        seed=simulation.seed,
        amount_minor=simulation.initial_payment.amount_minor,
        currency=simulation.initial_payment.currency,
        events=[_event_response(event) for event in simulation.events],
        result=_result_response(result),
    )


@router.post(
    "/{simulation_id}/counterexample",
    response_model=CounterexampleResponse,
)
async def create_counterexample(
    simulation_id: UUID,
    request: AttackRequest,
) -> CounterexampleResponse:
    """Create and deterministically shrink a failing adversarial simulation."""
    simulation = _simulations.get(simulation_id)

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found",
        )

    try:
        component = _build_attack(simulation, request)
        scenario = AdversarialScenarioComposer.compose(
            simulation,
            component,
        )
        execution = AdversarialScenarioExecutor.execute(
            simulation,
            scenario,
        )
    except (
        IndexError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    adversarial_simulation = execution.adversarial_simulation

    def reproduces_failure(candidate: PaymentSimulation) -> bool:
        try:
            PaymentSimulationRunner.run(candidate)
        except InvalidPaymentTransition:
            return True
        return False

    try:
        minimized = CounterexampleShrinker.shrink(
            adversarial_simulation,
            reproduces_failure,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Counterexample requires an adversarial simulation that "
                "reproduces a payment transition failure."
            ),
        ) from exc

    return CounterexampleResponse(
        simulation_id=minimized.id,
        violation_code="INVALID_PAYMENT_TRANSITION",
        original_event_count=len(adversarial_simulation.events),
        minimized_event_count=len(minimized.events),
        events=[
            CounterexampleEventResponse(
                id=event.id,
                sequence=event.sequence,
                event=event.event.value,
                occurred_at=event.occurred_at,
            )
            for event in minimized.events
        ],
    )

@router.post(
    "/{simulation_id}/attacks",
    response_model=AdversarialSimulationResponse,
)
async def execute_attack(
    simulation_id: UUID,
    request: AttackRequest,
) -> AdversarialSimulationResponse:
    """Execute a configured adversarial scenario against a simulation."""
    simulation = _simulations.get(simulation_id)

    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found",
        )

    try:
        component = _build_attack(simulation, request)
        scenario = AdversarialScenarioComposer.compose(
            simulation,
            component,
        )
        result = AdversarialScenarioExecutor.execute(
            simulation,
            scenario,
        )
    except (
        IndexError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    try:
        adversarial_result = result.adversarial_result
    except InvalidPaymentTransition as exc:
        attack_type = request.attack_type.strip().lower()

        if attack_type == "duplicate":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

        return AdversarialSimulationResponse(
            simulation_id=result.simulation_id,
            attack_count=result.attack_count,
            applied_components=list(result.applied_components),
            outcomes=[
                AttackOutcomeResponse(
                    component_type=outcome.component_type,
                    target_sequence=outcome.target_sequence,
                    status=outcome.status,
                )
                for outcome in result.outcomes
            ],
            baseline=_result_response(result.baseline),
            adversarial=None,
            adversarial_status="failed",
            failure=AdversarialFailureResponse(
                failure_type=type(exc).__name__,
                message=str(exc),
            ),
        )

    return AdversarialSimulationResponse(
        simulation_id=result.simulation_id,
        attack_count=result.attack_count,
        applied_components=list(result.applied_components),
        outcomes=[
            AttackOutcomeResponse(
                component_type=outcome.component_type,
                target_sequence=outcome.target_sequence,
                status=outcome.status,
            )
            for outcome in result.outcomes
        ],
        baseline=_result_response(result.baseline),
        adversarial=_result_response(adversarial_result),
        adversarial_status="completed",
        failure=None,
    )


