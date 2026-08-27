from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard successful API response envelope."""

    success: bool = True
    data: T


class ErrorDetail(BaseModel):
    """Structured API error information."""

    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=500)


class ErrorResponse(BaseModel):
    """Standard API error response envelope."""

    success: bool = False
    error: ErrorDetail


class HealthResponse(BaseModel):
    """Health endpoint response."""

    model_config = ConfigDict(extra="forbid")

    status: str


class ReadinessResponse(BaseModel):
    """Readiness endpoint response."""

    model_config = ConfigDict(extra="forbid")

    status: str