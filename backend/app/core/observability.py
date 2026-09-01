from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import structlog

OBSERVABILITY_FIELDS = (
    "correlation_id",
    "trace_id",
    "simulation_id",
    "contract_id",
    "verification_id",
    "counterexample_id",
)


def bind_observability_context(
    *,
    correlation_id: str | None = None,
    trace_id: str | None = None,
    simulation_id: str | None = None,
    contract_id: str | None = None,
    verification_id: str | None = None,
    counterexample_id: str | None = None,
) -> None:
    """Bind non-null observability identifiers to the current context."""

    values = {
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "simulation_id": simulation_id,
        "contract_id": contract_id,
        "verification_id": verification_id,
        "counterexample_id": counterexample_id,
    }

    bind_context_fields(values)


def bind_context_fields(
    fields: Mapping[str, Any],
) -> None:
    """Bind supported observability fields to the current context."""

    values = {
        key: value
        for key, value in fields.items()
        if key in OBSERVABILITY_FIELDS and value is not None
    }

    if values:
        structlog.contextvars.bind_contextvars(**values)


def get_observability_context() -> dict[str, Any]:
    """Return the currently bound observability context."""

    context = structlog.contextvars.get_contextvars()

    return {
        key: context[key]
        for key in OBSERVABILITY_FIELDS
        if key in context
    }


def clear_observability_context() -> None:
    """Clear all observability context fields."""

    context = structlog.contextvars.get_contextvars()

    for key in OBSERVABILITY_FIELDS:
        if key in context:
            structlog.contextvars.unbind_contextvars(key)
