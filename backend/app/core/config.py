"""Application configuration."""

from decimal import Decimal
from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application configuration."""

    app_name: str = "Financial Proof API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False

    proof_minimum_review_confidence: Decimal = Decimal("0.00")
    proof_minimum_ready_confidence: Decimal = Decimal("0.70")
    proof_minimum_supported_claim_ratio: Decimal = Decimal("1.00")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: SecretStr = SecretStr("sqlite:///./financial_proof.db")

    api_auth_token: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        """Validate application and proof-evaluation configuration."""

        normalized_environment = self.app_env.strip().lower()

        if normalized_environment not in {
            "development",
            "test",
            "staging",
            "production",
        }:
            raise ValueError(
                "APP_ENV must be one of: development, test, staging, production."
            )

        if not (
            Decimal("0") <= self.proof_minimum_review_confidence <= Decimal("1")
        ):
            raise ValueError(
                "Proof minimum review confidence must be between 0 and 1."
            )

        if not (
            Decimal("0") <= self.proof_minimum_ready_confidence <= Decimal("1")
        ):
            raise ValueError(
                "Proof minimum ready confidence must be between 0 and 1."
            )

        if not (
            Decimal("0") <= self.proof_minimum_supported_claim_ratio <= Decimal("1")
        ):
            raise ValueError(
                "Proof minimum supported claim ratio must be between 0 and 1."
            )

        if (
            self.proof_minimum_review_confidence
            > self.proof_minimum_ready_confidence
        ):
            raise ValueError(
                "Proof minimum review confidence cannot exceed "
                "proof minimum ready confidence."
            )

        if normalized_environment == "production":
            if self.debug:
                raise ValueError(
                    "DEBUG must be false in production."
                )

            if self.api_auth_token is None:
                raise ValueError(
                    "API_AUTH_TOKEN is required in production."
                )

        self.app_env = normalized_environment
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached application configuration."""

    return Settings()


settings = get_settings()
