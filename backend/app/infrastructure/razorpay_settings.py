"""Razorpay infrastructure configuration."""

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RazorpaySettings(BaseSettings):
    """Configuration required by the Razorpay payment adapter."""

    key_id: str
    key_secret: SecretStr
    timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(
        env_prefix="RAZORPAY_",
        extra="ignore",
    )

    @field_validator("key_id")
    @classmethod
    def validate_key_id(cls, value: str) -> str:
        """Reject an empty Razorpay key ID."""

        if not value.strip():
            raise ValueError("Razorpay key ID cannot be empty.")

        return value

    @field_validator("key_secret")
    @classmethod
    def validate_key_secret(cls, value: SecretStr) -> SecretStr:
        """Reject an empty Razorpay key secret."""

        if not value.get_secret_value().strip():
            raise ValueError("Razorpay key secret cannot be empty.")

        return value

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: float) -> float:
        """Require a positive provider timeout."""

        if value <= 0:
            raise ValueError("Razorpay timeout must be greater than zero.")

        return value
