from decimal import Decimal
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Financial Proof API"
    app_version: str = "0.1.0"
    debug: bool = True

    proof_minimum_review_confidence: Decimal = Decimal("0.00")
    proof_minimum_ready_confidence: Decimal = Decimal("0.70")
    proof_minimum_supported_claim_ratio: Decimal = Decimal("1.00")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = (
        "postgresql+psycopg://financial_proof:financial_proof"
        "@localhost:5433/financial_proof"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_proof_evaluation_policy(self) -> "Settings":
        """Validate proof evaluation threshold relationships."""
        if not Decimal("0") <= self.proof_minimum_review_confidence <= Decimal("1"):
            raise ValueError(
                "Proof minimum review confidence must be between 0 and 1."
            )

        if not Decimal("0") <= self.proof_minimum_ready_confidence <= Decimal("1"):
            raise ValueError(
                "Proof minimum ready confidence must be between 0 and 1."
            )

        if not Decimal("0") <= self.proof_minimum_supported_claim_ratio <= Decimal("1"):
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

        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


