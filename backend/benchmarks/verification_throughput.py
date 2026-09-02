"""Reproducible verification throughput benchmarks."""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.models.verification_snapshot import VerificationSnapshot
from app.domain.services.verification import VerificationService
from app.domain.services.verification_comparison import (
    VerificationComparisonService,
)
from benchmarks.harness import benchmark

RESULTS_PATH = Path("benchmarks/results")


def _build_comparison(*, regression: bool):
    if regression:
        before = VerificationSnapshot(
            contract_version="1",
            system_version="1",
            violations=(),
        )
        after = VerificationSnapshot(
            contract_version="1",
            system_version="1",
            violations=("duplicate_charge",),
        )
    else:
        before = VerificationSnapshot(
            contract_version="1",
            system_version="1",
            violations=("refund_without_approval",),
        )
        after = VerificationSnapshot(
            contract_version="1",
            system_version="1",
            violations=(),
        )

    return VerificationComparisonService.compare(
        before,
        after,
    )


def run_benchmark(
    *,
    verification_count: int,
    warmups: int = 2,
    iterations: int = 5,
) -> dict[str, object]:
    """Run deterministic verification throughput benchmarks."""
    if verification_count < 1:
        raise ValueError("verification_count must be at least 1.")

    clean_comparison = _build_comparison(regression=False)
    regression_comparison = _build_comparison(regression=True)

    clean_result, clean_outputs = benchmark(
        name="verification_clean",
        workload_size=verification_count,
        operation=lambda: tuple(
            VerificationService.verify(clean_comparison)
            for _ in range(verification_count)
        ),
        warmups=warmups,
        iterations=iterations,
    )

    regression_result, regression_outputs = benchmark(
        name="verification_regression",
        workload_size=verification_count,
        operation=lambda: tuple(
            VerificationService.verify(regression_comparison)
            for _ in range(verification_count)
        ),
        warmups=warmups,
        iterations=iterations,
    )

    for outputs in (clean_outputs, regression_outputs):
        for output in outputs:
            if len(output) != verification_count:
                raise RuntimeError(
                    "Verification benchmark returned an unexpected "
                    "number of results."
                )

    payload = {
        "workload": {
            "verification_count": verification_count,
        },
        "clean": clean_result.as_dict(),
        "regression": regression_result.as_dict(),
    }

    RESULTS_PATH.mkdir(parents=True, exist_ok=True)

    output_path = RESULTS_PATH / (
        f"verification_{verification_count}.json"
    )
    output_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return payload


if __name__ == "__main__":
    payload = run_benchmark(
        verification_count=1000,
    )
    print(json.dumps(payload, indent=2))
