"""Deterministic demo lifecycle API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.demo import get_demo_state_manager
from app.demo.state import DemoStateManager

router = APIRouter(prefix="/demo", tags=["demo"])

DemoManager = Annotated[DemoStateManager, Depends(get_demo_state_manager)]


@router.get("/state")
def get_demo_state(manager: DemoManager) -> dict[str, object]:
    """Return the current deterministic demo state summary."""
    return {
        "success": True,
        "state": manager.snapshot(),
    }


@router.post("/reset")
def reset_demo(manager: DemoManager) -> dict[str, object]:
    """Reset the demo to its canonical deterministic starting state."""
    state = manager.reset()

    return {
        "success": True,
        "message": "Demo state reset.",
        "state": manager.snapshot(),
        "simulation_id": str(state.seed.simulation_id),
    }


@router.post("/replay")
def replay_demo(manager: DemoManager) -> dict[str, object]:
    """Reset the demo and return a fresh deterministic replay context."""
    state = manager.reset()

    return {
        "success": True,
        "message": "Demo replay initialized.",
        "state": manager.snapshot(),
        "seed": state.seed.seed,
        "simulation_id": str(state.seed.simulation_id),
        "event_count": len(state.seed.events),
    }
