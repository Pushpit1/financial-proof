"""Sensitive-data redaction primitives."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

REDACTED_VALUE = "[REDACTED]"

SENSITIVE_FIELD_NAMES = frozenset(
    {
        "authorization",
        "api_key",
        "apikey",
        "key_secret",
        "password",
        "payload",
        "request_body",
        "secret",
        "signature",
        "token",
    }
)


def is_sensitive_field(name: str) -> bool:
    """Return whether a field name must never be logged verbatim."""
    normalized = name.strip().lower().replace("-", "_")
    return normalized in SENSITIVE_FIELD_NAMES or any(
        sensitive in normalized
        for sensitive in (
            "authorization",
            "password",
            "secret",
            "token",
            "api_key",
            "signature",
        )
    )


def redact_sensitive_data(value: Any) -> Any:
    """Recursively redact sensitive mapping fields before logging."""
    if isinstance(value, Mapping):
        return {
            key: (
                REDACTED_VALUE
                if isinstance(key, str) and is_sensitive_field(key)
                else redact_sensitive_data(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return tuple(redact_sensitive_data(item) for item in value)

    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return type(value)(
            redact_sensitive_data(item)
            for item in value
        )

    return value

