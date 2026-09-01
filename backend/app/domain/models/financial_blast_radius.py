from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4


class FinancialBlastRadiusSeverity(StrEnum):
    """Ordered severity levels for financial exposure."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class FinancialExposure:
    """One monetary exposure identified by a financial violation."""

    field: str
    amount: Decimal
    currency: str
    source_violation_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ValueError("Financial exposure field cannot be empty.")

        if self.field != self.field.strip():
            raise ValueError(
                "Financial exposure field cannot contain surrounding whitespace."
            )

        if self.amount < Decimal("0"):
            raise ValueError("Financial exposure amount cannot be negative.")

        normalized_currency = self.currency.upper()

        if len(normalized_currency) != 3:
            raise ValueError(
                "Financial exposure currency must be a 3-letter ISO code."
            )

        if not normalized_currency.isalpha():
            raise ValueError(
                "Financial exposure currency must contain only letters."
            )

        object.__setattr__(self, "currency", normalized_currency)


@dataclass(frozen=True)
class FinancialBlastRadiusSeverityPolicy:
    """Explicit deterministic thresholds for blast-radius severity."""

    low_threshold: Decimal
    medium_threshold: Decimal
    high_threshold: Decimal
    critical_threshold: Decimal

    def __post_init__(self) -> None:
        thresholds = (
            self.low_threshold,
            self.medium_threshold,
            self.high_threshold,
            self.critical_threshold,
        )

        if any(threshold < Decimal("0") for threshold in thresholds):
            raise ValueError("Severity thresholds cannot be negative.")

        if not (
            self.low_threshold
            <= self.medium_threshold
            <= self.high_threshold
            <= self.critical_threshold
        ):
            raise ValueError(
                "Severity thresholds must be monotonically increasing."
            )

    def classify(self, amount: Decimal) -> FinancialBlastRadiusSeverity:
        if amount < self.low_threshold:
            return FinancialBlastRadiusSeverity.NONE

        if amount < self.medium_threshold:
            return FinancialBlastRadiusSeverity.LOW

        if amount < self.high_threshold:
            return FinancialBlastRadiusSeverity.MEDIUM

        if amount < self.critical_threshold:
            return FinancialBlastRadiusSeverity.HIGH

        return FinancialBlastRadiusSeverity.CRITICAL


_SEVERITY_RANK = {
    FinancialBlastRadiusSeverity.NONE: 0,
    FinancialBlastRadiusSeverity.LOW: 1,
    FinancialBlastRadiusSeverity.MEDIUM: 2,
    FinancialBlastRadiusSeverity.HIGH: 3,
    FinancialBlastRadiusSeverity.CRITICAL: 4,
}


@dataclass(frozen=True)
class FinancialBlastRadius:
    """Immutable aggregate describing the financial impact of violations."""

    source_id: UUID
    exposures: tuple[FinancialExposure, ...] = ()
    affected_fields: tuple[str, ...] = ()

    @property
    def exposure_count(self) -> int:
        return len(self.exposures)

    @property
    def total_exposure_by_currency(self) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}

        for exposure in self.exposures:
            totals[exposure.currency] = (
                totals.get(exposure.currency, Decimal("0"))
                + exposure.amount
            )

        return totals

    @property
    def total_exposure(self) -> Decimal:
        """Return total exposure when all exposures share one currency."""

        currencies = {exposure.currency for exposure in self.exposures}

        if len(currencies) > 1:
            raise ValueError(
                "Total exposure cannot combine multiple currencies."
            )

        return sum(
            (exposure.amount for exposure in self.exposures),
            Decimal("0"),
        )

    @property
    def currencies(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    exposure.currency
                    for exposure in self.exposures
                }
            )
        )

    def severity(
        self,
        policy: FinancialBlastRadiusSeverityPolicy,
    ) -> FinancialBlastRadiusSeverity:
        """Classify exposure using an explicit policy."""

        if self.exposure_count == 0:
            return FinancialBlastRadiusSeverity.NONE

        if len(self.currencies) != 1:
            raise ValueError(
                "Severity cannot combine exposures from multiple currencies."
            )

        return policy.classify(self.total_exposure)

    def ranked_exposures(
        self,
        policy: FinancialBlastRadiusSeverityPolicy,
    ) -> tuple[FinancialExposure, ...]:
        """Return exposures in deterministic descending impact order.

        Exposures are never compared across currencies. Currency partitions
        are sorted alphabetically, and exposures within each currency are
        ordered by severity, amount, field, and UUID.
        """

        def sort_key(
            exposure: FinancialExposure,
        ) -> tuple[str, int, Decimal, str, str]:
            severity = policy.classify(exposure.amount)

            return (
                exposure.currency,
                -_SEVERITY_RANK[severity],
                -exposure.amount,
                exposure.field,
                str(exposure.id),
            )

        return tuple(sorted(self.exposures, key=sort_key))

    @classmethod
    def from_exposures(
        cls,
        source_id: UUID,
        exposures: tuple[FinancialExposure, ...],
    ) -> "FinancialBlastRadius":
        affected_fields = tuple(
            dict.fromkeys(
                exposure.field
                for exposure in exposures
            )
        )

        return cls(
            source_id=source_id,
            exposures=exposures,
            affected_fields=affected_fields,
        )
