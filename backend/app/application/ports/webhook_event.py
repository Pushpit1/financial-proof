from abc import ABC, abstractmethod

from app.domain.models.webhook import WebhookEvent


class WebhookEventRepositoryPort(ABC):
    """Application boundary for persisted webhook events."""

    @abstractmethod
    def add(self, event: WebhookEvent) -> None:
        """Persist a webhook event."""
        raise NotImplementedError

    @abstractmethod
    def get_by_provider_event_id(
        self,
        provider: str,
        provider_event_id: str,
    ) -> WebhookEvent | None:
        """Retrieve a webhook event by provider-specific event ID."""
        raise NotImplementedError

    @abstractmethod
    def mark_processed(self, event: WebhookEvent) -> None:
        """Persist the processed state of a webhook event."""
        raise NotImplementedError
