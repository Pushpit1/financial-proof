from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CounterexampleEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    sequence: int
    event: str
    occurred_at: datetime


class CounterexampleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: UUID
    violation_code: str
    original_event_count: int
    minimized_event_count: int
    events: list[CounterexampleEventResponse]
