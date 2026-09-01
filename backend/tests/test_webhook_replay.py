import pytest

from app.application.ports.webhook_replay import (
    InMemoryWebhookReplayStore,
)


def test_replay_store_claims_event_once() -> None:
    store = InMemoryWebhookReplayStore()

    assert store.claim("evt_123") is True
    assert store.claim("evt_123") is False


def test_replay_store_normalizes_event_id() -> None:
    store = InMemoryWebhookReplayStore()

    assert store.claim("  evt_123  ") is True
    assert store.claim("evt_123") is False


def test_replay_store_rejects_blank_event_id() -> None:
    store = InMemoryWebhookReplayStore()

    with pytest.raises(
        ValueError,
        match="Webhook event ID cannot be empty",
    ):
        store.claim("   ")
