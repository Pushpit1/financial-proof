"""Canonical deterministic seed data for the Financial Proof demo."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid5

from app.domain.enums.financial import ClaimType
from app.domain.enums.payment import PaymentEvent
from app.domain.models.payment import Payment, PaymentOrder
from app.domain.models.payment_simulation import (
    PaymentSimulation,
    SimulationEvent,
)

DEMO_NAMESPACE = UUID("7c7a2d3a-4f2b-4b5e-9f11-6a4d5f8e9c21")

DEMO_CONTRACT_ID = uuid5(DEMO_NAMESPACE, "contract:refund-safety:v1")
DEMO_ORDER_ID = uuid5(DEMO_NAMESPACE, "order:refund-safety")
DEMO_PAYMENT_ID = uuid5(DEMO_NAMESPACE, "payment:refund-safety")
DEMO_SIMULATION_ID = uuid5(DEMO_NAMESPACE, "simulation:refund-safety")

DEMO_EVENT_AUTHORIZE_ID = uuid5(
    DEMO_NAMESPACE,
    "simulation:event:0:authorize",
)
DEMO_EVENT_CAPTURE_ID = uuid5(
    DEMO_NAMESPACE,
    "simulation:event:1:capture",
)

DEMO_SEED = 20260902
DEMO_AMOUNT_MINOR = 5000
DEMO_CURRENCY = "INR"

DEMO_START_TIME = datetime(
    2026,
    9,
    2,
    12,
    0,
    0,
    tzinfo=UTC,
)

DEMO_BUSINESS_RULE = (
    "A customer refund must never exceed the original payment amount."
)

DEMO_CONTRACT_NAME = "customer-refund-safety"

DEMO_VIOLATION_CONTEXT = {
    "original_payment_amount": Decimal("50.00"),
    "refund_amount": Decimal("75.00"),
    "currency": DEMO_CURRENCY,
}

DEMO_UNAUTHORIZED_ACTOR = "demo-unauthorized-operator"
DEMO_AUTHORIZED_ACTOR = "demo-finance-operator"


@dataclass(frozen=True)
class DemoSeed:
    """Immutable canonical input set for the end-to-end demo."""

    seed: int
    contract_id: UUID
    contract_name: str
    contract_version: int
    business_rule: str
    required_claim_types: tuple[ClaimType, ...]
    order_id: UUID
    payment_id: UUID
    simulation_id: UUID
    amount_minor: int
    currency: str
    start_time: datetime
    events: tuple[SimulationEvent, ...]
    violation_context: dict[str, object]
    unauthorized_actor: str
    authorized_actor: str

    def build_payment(self) -> Payment:
        """Build the deterministic initial payment aggregate."""
        return Payment(
            id=self.payment_id,
            order_id=self.order_id,
            amount_minor=self.amount_minor,
            currency=self.currency,
            created_at=self.start_time,
        )

    def build_order(self) -> PaymentOrder:
        """Build the deterministic initial order aggregate."""
        return PaymentOrder(
            id=self.order_id,
            amount_minor=self.amount_minor,
            currency=self.currency,
            created_at=self.start_time,
        )

    def build_simulation(self) -> PaymentSimulation:
        """Build the deterministic baseline payment simulation."""
        return PaymentSimulation(
            id=self.simulation_id,
            seed=self.seed,
            initial_payment=self.build_payment(),
            initial_order=self.build_order(),
            events=self.events,
        )


def build_demo_seed() -> DemoSeed:
    """Return the canonical deterministic demo dataset."""
    events = (
        SimulationEvent(
            id=DEMO_EVENT_AUTHORIZE_ID,
            sequence=0,
            event=PaymentEvent.AUTHORIZE,
            occurred_at=DEMO_START_TIME,
        ),
        SimulationEvent(
            id=DEMO_EVENT_CAPTURE_ID,
            sequence=1,
            event=PaymentEvent.CAPTURE,
            occurred_at=DEMO_START_TIME + timedelta(seconds=1),
        ),
    )

    return DemoSeed(
        seed=DEMO_SEED,
        contract_id=DEMO_CONTRACT_ID,
        contract_name=DEMO_CONTRACT_NAME,
        contract_version=1,
        business_rule=DEMO_BUSINESS_RULE,
        required_claim_types=(ClaimType.TRANSACTION,),
        order_id=DEMO_ORDER_ID,
        payment_id=DEMO_PAYMENT_ID,
        simulation_id=DEMO_SIMULATION_ID,
        amount_minor=DEMO_AMOUNT_MINOR,
        currency=DEMO_CURRENCY,
        start_time=DEMO_START_TIME,
        events=events,
        violation_context=dict(DEMO_VIOLATION_CONTEXT),
        unauthorized_actor=DEMO_UNAUTHORIZED_ACTOR,
        authorized_actor=DEMO_AUTHORIZED_ACTOR,
    )


__all__ = [
    "DEMO_AMOUNT_MINOR",
    "DEMO_AUTHORIZED_ACTOR",
    "DEMO_BUSINESS_RULE",
    "DEMO_CONTRACT_ID",
    "DEMO_CONTRACT_NAME",
    "DEMO_CURRENCY",
    "DEMO_NAMESPACE",
    "DEMO_ORDER_ID",
    "DEMO_PAYMENT_ID",
    "DEMO_SEED",
    "DEMO_SIMULATION_ID",
    "DEMO_START_TIME",
    "DEMO_UNAUTHORIZED_ACTOR",
    "DEMO_VIOLATION_CONTEXT",
    "DemoSeed",
    "build_demo_seed",
]
