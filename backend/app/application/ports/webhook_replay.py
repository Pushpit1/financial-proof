from abc import ABC, abstractmethod


class ReplayDetectedError(ValueError):
    """Raised when a previously processed event is received again."""


class WebhookReplayStore(ABC):
    """Application boundary for webhook replay protection."""

    @abstractmethod
    def claim(self, event_id: str) -> bool:
        """Atomically claim an event ID."""
        raise NotImplementedError


class InMemoryWebhookReplayStore(WebhookReplayStore):
    """Process-local replay store used by the current application boundary."""

    def __init__(self) -> None:
        self._event_ids: set[str] = set()

    def claim(self, event_id: str) -> bool:
        """Claim an event ID exactly once."""
        normalized = event_id.strip()

        if not normalized:
            raise ValueError("Webhook event ID cannot be empty.")

        if normalized in self._event_ids:
            return False

        self._event_ids.add(normalized)
        return True
