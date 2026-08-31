from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class WebhookEvent:
    """Persisted record of an externally received webhook event."""

    provider: str
    provider_event_id: str
    event_type: str
    payload: bytes
    received_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    processed_at: datetime | None = None
    id: UUID = field(default_factory=uuid4)

    @property
    def is_processed(self) -> bool:
        """Return whether this webhook event has been processed."""
        return self.processed_at is not None

    def mark_processed(self) -> None:
        """Mark this webhook event as successfully processed."""
        if self.processed_at is not None:
            raise ValueError("Webhook event is already processed.")

        self.processed_at = datetime.now(UTC)
