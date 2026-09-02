from decimal import Decimal

from app.demo.pipeline import DemoPipeline
from app.demo.seed import build_demo_seed


def test_demo_pipeline_calculates_financial_exposure() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    blast_radius = pipeline.calculate_financial_exposure(contract)

    assert blast_radius.exposure_count == 1
    assert blast_radius.affected_fields == ("refund_amount",)
    assert blast_radius.total_exposure == Decimal("75.00")
    assert blast_radius.total_exposure_by_currency == {
        "INR": Decimal("75.00"),
    }

    exposure = blast_radius.exposures[0]

    assert exposure.field == "refund_amount"
    assert exposure.amount == Decimal("75.00")
    assert exposure.currency == "INR"
    assert exposure.direct_loss == Decimal("75.00")
    assert exposure.actual_exposure == Decimal("75.00")
    assert exposure.maximum_exposure == Decimal("75.00")
    assert exposure.duplicate_charge_exposure == Decimal("0")
    assert exposure.duplicate_fulfillment_exposure == Decimal("0")
    assert exposure.refund_exposure == Decimal("0")
    assert exposure.unauthorized_action_exposure == Decimal("0")


def test_demo_pipeline_financial_exposure_is_deterministic() -> None:
    seed = build_demo_seed()
    contract = DemoPipeline(seed).compile_contract()

    first = DemoPipeline(seed).calculate_financial_exposure(contract)
    second = DemoPipeline(seed).calculate_financial_exposure(contract)

    assert first.exposure_count == second.exposure_count
    assert first.total_exposure == second.total_exposure
    assert first.total_exposure_by_currency == (
        second.total_exposure_by_currency
    )

    first_exposure = first.exposures[0]
    second_exposure = second.exposures[0]

    assert first_exposure.field == second_exposure.field
    assert first_exposure.amount == second_exposure.amount
    assert first_exposure.currency == second_exposure.currency
    assert first_exposure.direct_loss == second_exposure.direct_loss
    assert first_exposure.actual_exposure == second_exposure.actual_exposure
    assert first_exposure.maximum_exposure == second_exposure.maximum_exposure


def test_demo_pipeline_exposure_uses_violation_context() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    blast_radius = pipeline.calculate_financial_exposure(contract)
    exposure = blast_radius.exposures[0]

    assert seed.violation_context["refund_amount"] == Decimal("75.00")
    assert exposure.amount == seed.violation_context["refund_amount"]


def test_demo_pipeline_exposure_explains_failed_constraint() -> None:
    seed = build_demo_seed()
    pipeline = DemoPipeline(seed)
    contract = pipeline.compile_contract()

    blast_radius = pipeline.calculate_financial_exposure(contract)
    exposure = blast_radius.exposures[0]

    assert exposure.explanation == (
        "Financial constraint on 'refund_amount' failed; "
        "direct financial exposure is 75.00 INR."
    )
