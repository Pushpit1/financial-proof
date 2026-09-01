import json

from app.core.logging import configure_logging
from app.domain.services.counterexample_chunk_shrinker import (
    CounterexampleChunkShrinker,
)
from app.domain.services.counterexample_shrinker import CounterexampleShrinker
from tests.test_counterexample_shrinker import make_simulation


def _log_events(captured: str) -> list[dict[str, object]]:
    events = []

    for line in captured.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        if "event" in payload:
            events.append(payload)

    return events


def test_counterexample_shrinker_emits_observability_events(capsys) -> None:
    configure_logging()

    simulation = make_simulation()

    result = CounterexampleShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    events = _log_events(capsys.readouterr().out)

    started = next(
        event
        for event in events
        if event["event"] == "counterexample_shrink_started"
    )
    completed = next(
        event
        for event in events
        if event["event"] == "counterexample_shrink_completed"
    )

    assert started["simulation_id"] == str(simulation.id)
    assert started["original_event_count"] == len(simulation.events)
    assert completed["simulation_id"] == str(simulation.id)
    assert completed["minimized_event_count"] == len(result.events)


def test_counterexample_chunk_shrinker_emits_observability_events(
    capsys,
) -> None:
    configure_logging()

    simulation = make_simulation()

    result = CounterexampleChunkShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    events = _log_events(capsys.readouterr().out)

    started = next(
        event
        for event in events
        if event["event"] == "counterexample_chunk_shrink_started"
    )
    completed = next(
        event
        for event in events
        if event["event"] == "counterexample_chunk_shrink_completed"
    )

    assert started["simulation_id"] == str(simulation.id)
    assert started["original_event_count"] == len(simulation.events)
    assert completed["simulation_id"] == str(simulation.id)
    assert completed["minimized_event_count"] == len(result.events)


def test_counterexample_shrinker_preserves_observability_context() -> None:
    simulation = make_simulation()

    CounterexampleShrinker.shrink(
        simulation,
        lambda candidate: len(candidate.events) >= 2,
    )

    from app.core.observability import get_observability_context

    context = get_observability_context()

    assert context["simulation_id"] == str(simulation.id)
