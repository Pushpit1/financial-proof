"""Tests for sensitive-data redaction."""

import json

import structlog

from app.core.logging import log_event
from app.core.redaction import REDACTED_VALUE, redact_sensitive_data


def test_redacts_sensitive_mapping_fields_recursively() -> None:
    value = {
        "correlation_id": "corr-123",
        "authorization": "Bearer super-secret-token",
        "nested": {
            "api_key": "api-secret",
            "safe": "visible",
            "request": {
                "signature": "webhook-secret",
                "amount": 5000,
            },
        },
    }

    result = redact_sensitive_data(value)

    assert result == {
        "correlation_id": "corr-123",
        "authorization": REDACTED_VALUE,
        "nested": {
            "api_key": REDACTED_VALUE,
            "safe": "visible",
            "request": {
                "signature": REDACTED_VALUE,
                "amount": 5000,
            },
        },
    }


def test_redacts_sensitive_field_name_variants() -> None:
    result = redact_sensitive_data(
        {
            "Authorization": "Bearer secret",
            "x-api-key": "secret-key",
            "key-secret": "secret-value",
            "access_token": "access-secret",
            "password": "password-value",
        }
    )

    assert result["Authorization"] == REDACTED_VALUE
    assert result["x-api-key"] == REDACTED_VALUE
    assert result["key-secret"] == REDACTED_VALUE
    assert result["access_token"] == REDACTED_VALUE
    assert result["password"] == REDACTED_VALUE


def test_preserves_non_sensitive_values() -> None:
    value = {
        "correlation_id": "corr-123",
        "operation": "refund",
        "amount_minor": 5000,
    }

    assert redact_sensitive_data(value) == value


def test_redacts_nested_collections() -> None:
    value = [
        {"token": "secret"},
        ("safe", {"signature": "secret"}),
    ]

    result = redact_sensitive_data(value)

    assert result == [
        {"token": REDACTED_VALUE},
        ("safe", {"signature": REDACTED_VALUE}),
    ]


def test_log_event_redacts_sensitive_fields(
    capsys,
) -> None:
    logger = structlog.get_logger("redaction-test")

    log_event(
        logger,
        "security_event",
        fields={
            "correlation_id": "corr-123",
            "authorization": "Bearer super-secret",
            "token": "super-secret-token",
            "signature": "webhook-secret",
            "operation": "refund",
        },
    )

    output = capsys.readouterr().out

    assert "super-secret" not in output
    assert "super-secret-token" not in output
    assert "webhook-secret" not in output
    assert REDACTED_VALUE in output
    assert "corr-123" in output
    assert "refund" in output


def test_redaction_result_is_json_serializable() -> None:
    result = redact_sensitive_data(
        {
            "authorization": "Bearer secret",
            "nested": {"token": "secret"},
        }
    )

    encoded = json.dumps(result)

    assert REDACTED_VALUE in encoded
