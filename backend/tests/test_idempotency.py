from app.domain.models.idempotency import (
    IdempotencyKey,
    IdempotencyRecord,
)
from app.domain.services.idempotency import (
    DuplicateIdempotencyKey,
    IdempotencyService,
)


def test_idempotency_key_rejects_empty_value() -> None:
    import pytest

    with pytest.raises(ValueError):
        IdempotencyKey(value="   ")


def test_idempotency_record_rejects_empty_fingerprint() -> None:
    import pytest

    with pytest.raises(ValueError):
        IdempotencyRecord(
            key=IdempotencyKey("request-1"),
            response_fingerprint="",
        )


def test_idempotency_record_can_be_stored() -> None:
    service = IdempotencyService()

    record = IdempotencyRecord(
        key=IdempotencyKey("request-1"),
        response_fingerprint="fingerprint-1",
    )

    result = service.record(record)

    assert result == record
    assert service.lookup(record.key) == record


def test_same_idempotency_record_is_replayed() -> None:
    service = IdempotencyService()

    record = IdempotencyRecord(
        key=IdempotencyKey("request-1"),
        response_fingerprint="fingerprint-1",
    )

    first = service.record(record)
    second = service.record(record)

    assert first == second


def test_conflicting_idempotency_key_is_rejected() -> None:
    service = IdempotencyService()

    first = IdempotencyRecord(
        key=IdempotencyKey("request-1"),
        response_fingerprint="fingerprint-1",
    )

    second = IdempotencyRecord(
        key=IdempotencyKey("request-1"),
        response_fingerprint="fingerprint-2",
    )

    service.record(first)

    import pytest

    with pytest.raises(DuplicateIdempotencyKey):
        service.record(second)
