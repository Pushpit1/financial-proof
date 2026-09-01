import structlog

from app.core.observability import (
    bind_context_fields,
    bind_observability_context,
    clear_observability_context,
    get_observability_context,
)


def test_bind_observability_context_binds_all_identifiers() -> None:
    structlog.contextvars.clear_contextvars()

    bind_observability_context(
        correlation_id="corr-1",
        trace_id="trace-1",
        simulation_id="sim-1",
        contract_id="contract-1",
        verification_id="verification-1",
        counterexample_id="counterexample-1",
    )

    assert get_observability_context() == {
        "correlation_id": "corr-1",
        "trace_id": "trace-1",
        "simulation_id": "sim-1",
        "contract_id": "contract-1",
        "verification_id": "verification-1",
        "counterexample_id": "counterexample-1",
    }


def test_none_values_are_not_bound() -> None:
    structlog.contextvars.clear_contextvars()

    bind_observability_context(
        correlation_id="corr-1",
        simulation_id=None,
        verification_id=None,
    )

    assert get_observability_context() == {
        "correlation_id": "corr-1",
    }


def test_arbitrary_context_fields_are_rejected() -> None:
    structlog.contextvars.clear_contextvars()

    bind_context_fields(
        {
            "correlation_id": "corr-1",
            "not_an_observability_field": "secret",
        },
    )

    assert get_observability_context() == {
        "correlation_id": "corr-1",
    }


def test_clear_observability_context_removes_bound_fields() -> None:
    structlog.contextvars.clear_contextvars()

    bind_observability_context(
        correlation_id="corr-1",
        trace_id="trace-1",
        simulation_id="sim-1",
    )

    clear_observability_context()

    assert get_observability_context() == {}
