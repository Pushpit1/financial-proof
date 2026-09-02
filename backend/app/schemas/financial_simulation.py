"""API schemas for financial payment simulations and attack configuration."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SimulationEventRequest(BaseModel):
    """Event supplied when creating a simulation."""

    model_config = ConfigDict(extra="forbid")

    event: str
    occurred_at: datetime


class SimulationCreateRequest(BaseModel):
    """Request for creating a deterministic payment simulation."""

    model_config = ConfigDict(extra="forbid")

    seed: int
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    events: list[SimulationEventRequest] = Field(default_factory=list)


class SimulationEventResponse(BaseModel):
    """Simulation event with its stable event identifier."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    sequence: int
    event: str
    occurred_at: datetime


class SimulationTraceEntryResponse(BaseModel):
    """Execution trace entry produced by the simulation runner."""

    model_config = ConfigDict(extra="forbid")

    sequence: int
    event: str
    occurred_at: datetime


class SimulationStateResponse(BaseModel):
    """Payment and order state captured during simulation."""

    model_config = ConfigDict(extra="forbid")

    payment_state: str
    order_state: str


class SimulationResultResponse(BaseModel):
    """Completed simulation execution result."""

    model_config = ConfigDict(extra="forbid")

    simulation_id: UUID
    seed: int
    final_payment_state: str
    final_order_state: str
    trace: list[SimulationTraceEntryResponse]
    snapshots: list[SimulationStateResponse]


class SimulationResponse(BaseModel):
    """Simulation definition and completed baseline result."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    seed: int
    amount_minor: int
    currency: str
    events: list[SimulationEventResponse]
    result: SimulationResultResponse


class AttackRequest(BaseModel):
    """Request for applying an adversarial scenario."""

    model_config = ConfigDict(extra="forbid")

    attack_type: str
    target_sequence: int = Field(ge=0)
    retry_count: int | None = Field(default=None, ge=1)
    delay_seconds: int | None = Field(default=None, gt=0)
    worker_sequence: int | None = Field(default=None, ge=0)
    incoming_sequence: int | None = Field(default=None, ge=0)


class AttackOutcomeResponse(BaseModel):
    """Outcome of an applied adversarial component."""

    model_config = ConfigDict(extra="forbid")

    component_type: str
    target_sequence: int
    status: str


class AdversarialSimulationResponse(BaseModel):
    """Baseline and adversarial simulation results."""

    model_config = ConfigDict(extra="forbid")

    simulation_id: UUID
    attack_count: int
    applied_components: list[str]
    outcomes: list[AttackOutcomeResponse]
    baseline: SimulationResultResponse
    adversarial: SimulationResultResponse
