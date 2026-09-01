from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class FinancialExposure(BaseModel):
    """Immutable financial exposure produced by a failed financial rule."""

    model_config = ConfigDict(frozen=True)

    analysis_id: UUID = Field(default_factory=uuid4)
    source_violation_id: UUID | None = None
    field: str | None = None
    amount: Decimal = Field(default=Decimal("0"))
    currency: str | None = None
    explanation: str = ""

    direct_loss: Decimal = Field(default=Decimal("0"))
    duplicate_charge_exposure: Decimal = Field(default=Decimal("0"))
    duplicate_fulfillment_exposure: Decimal = Field(default=Decimal("0"))
    refund_exposure: Decimal = Field(default=Decimal("0"))
    unauthorized_action_exposure: Decimal = Field(default=Decimal("0"))

    actual_exposure: Decimal = Field(default=Decimal("0"))
    maximum_exposure: Decimal = Field(default=Decimal("0"))

    def __setattr__(self, name: str, value: object) -> None:
        if name in self.__class__.model_fields:
            raise AttributeError(
                f"{self.__class__.__name__} is frozen and cannot be modified."
            )
        super().__setattr__(name, value)

    def model_post_init(self, __context: object) -> None:
        monetary_fields = (
            "amount",
            "direct_loss",
            "duplicate_charge_exposure",
            "duplicate_fulfillment_exposure",
            "refund_exposure",
            "unauthorized_action_exposure",
            "actual_exposure",
            "maximum_exposure",
        )

        for field_name in monetary_fields:
            value = getattr(self, field_name)
            if value < Decimal("0"):
                raise ValueError(f"{field_name} cannot be negative.")

        calculated_actual = (
            self.direct_loss
            + self.duplicate_charge_exposure
            + self.duplicate_fulfillment_exposure
            + self.refund_exposure
            + self.unauthorized_action_exposure
        )

        if self.actual_exposure != calculated_actual:
            raise ValueError(
                "actual_exposure must equal the sum of exposure components."
            )

        if self.maximum_exposure < self.actual_exposure:
            raise ValueError(
                "maximum_exposure cannot be less than actual_exposure."
            )


class FinancialBlastRadius(BaseModel):
    """Immutable aggregate of financial exposures caused by an evaluation."""

    model_config = ConfigDict(frozen=True)

    analysis_id: UUID = Field(default_factory=uuid4)
    exposures: tuple[FinancialExposure, ...] = ()

    @property
    def exposure_count(self) -> int:
        return len(self.exposures)

    @property
    def affected_fields(self) -> tuple[str, ...]:
        return tuple(
            exposure.field
            for exposure in self.exposures
            if exposure.field is not None
        )

    @property
    def total_exposure(self) -> Decimal:
        return sum(
            (exposure.amount for exposure in self.exposures),
            Decimal("0"),
        )

    @property
    def total_exposure_by_currency(self) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}

        for exposure in self.exposures:
            if exposure.currency is None:
                continue

            totals[exposure.currency] = (
                totals.get(exposure.currency, Decimal("0"))
                + exposure.amount
            )

        return totals
