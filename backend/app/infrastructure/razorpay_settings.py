from pydantic_settings import BaseSettings, SettingsConfigDict


class RazorpaySettings(BaseSettings):
    """Configuration required by the Razorpay payment adapter."""

    key_id: str
    key_secret: str
    timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(
        env_prefix="RAZORPAY_",
        extra="ignore",
    )
