"""Mappings between blast-radius domain objects and persistence models."""

from app.db.models.financial_blast_radius import (
    FinancialBlastRadiusModel,
    FinancialExposureModel,
)
from app.domain.models.financial_blast_radius import (
    FinancialBlastRadius,
    FinancialExposure,
)


def financial_exposure_to_model(
    exposure: FinancialExposure,
    analysis_id,
) -> FinancialExposureModel:
    """Convert a financial exposure into persistence."""
    return FinancialExposureModel(
        id=exposure.analysis_id,
        analysis_id=analysis_id,
        source_violation_id=exposure.source_violation_id,
        field=exposure.field,
        amount=exposure.amount,
        currency=exposure.currency,
        explanation=exposure.explanation,
        direct_loss=exposure.direct_loss,
        duplicate_charge_exposure=exposure.duplicate_charge_exposure,
        duplicate_fulfillment_exposure=exposure.duplicate_fulfillment_exposure,
        refund_exposure=exposure.refund_exposure,
        unauthorized_action_exposure=exposure.unauthorized_action_exposure,
        actual_exposure=exposure.actual_exposure,
        maximum_exposure=exposure.maximum_exposure,
    )


def financial_blast_radius_to_model(
    analysis: FinancialBlastRadius,
) -> FinancialBlastRadiusModel:
    """Convert a blast-radius aggregate into persistence."""
    return FinancialBlastRadiusModel(
        id=analysis.analysis_id,
        exposures=[
            financial_exposure_to_model(
                exposure,
                analysis.analysis_id,
            )
            for exposure in analysis.exposures
        ],
    )


def financial_exposure_to_domain(
    model: FinancialExposureModel,
) -> FinancialExposure:
    """Convert persisted exposure into the domain."""
    return FinancialExposure(
        analysis_id=model.id,
        source_violation_id=model.source_violation_id,
        field=model.field,
        amount=model.amount,
        currency=model.currency,
        explanation=model.explanation,
        direct_loss=model.direct_loss,
        duplicate_charge_exposure=model.duplicate_charge_exposure,
        duplicate_fulfillment_exposure=model.duplicate_fulfillment_exposure,
        refund_exposure=model.refund_exposure,
        unauthorized_action_exposure=model.unauthorized_action_exposure,
        actual_exposure=model.actual_exposure,
        maximum_exposure=model.maximum_exposure,
    )


def financial_blast_radius_to_domain(
    model: FinancialBlastRadiusModel,
) -> FinancialBlastRadius:
    """Convert persisted blast-radius analysis into the domain."""
    return FinancialBlastRadius(
        analysis_id=model.id,
        exposures=tuple(
            financial_exposure_to_domain(exposure)
            for exposure in model.exposures
        ),
    )

