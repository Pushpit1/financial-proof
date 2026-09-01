from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VerificationChange(BaseModel):
    """Immutable deterministic record of one verification change."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    change_id: UUID
    field: str
    before: Any = None
    after: Any = None
    change_type: str
