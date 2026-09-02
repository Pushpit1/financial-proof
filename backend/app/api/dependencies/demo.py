"""Demo lifecycle API dependency providers."""

from functools import lru_cache

from app.demo.state import DemoStateManager


@lru_cache(maxsize=1)
def get_demo_state_manager() -> DemoStateManager:
    """Return the process-local deterministic demo state manager."""
    return DemoStateManager()
