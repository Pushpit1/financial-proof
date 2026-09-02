"""API tests for deterministic before/after verification."""

from uuid import uuid4


def _snapshot(
    *,
    contract_version: str = "1",
    system_version: str = "1.0.0",
    violations: list[str] | None = None,
) -> dict:
    """Build a valid verification snapshot request."""
    return {
        "contract_version": contract_version,
        "system_version": system_version,
        "baseline": {
            "balance": 1000,
            "status": "active",
        },
        "violations": violations or [],
        "counterexample_ids": [],
        "reproducibility_metadata": {
            "seed": 42,
        },
    }


def test_verification_api_passes_without_regression(client) -> None:
    response = client.post(
        "/verification",
        json={
            "before": _snapshot(
                violations=["refund_without_approval"],
            ),
            "after": _snapshot(),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["result"]["passed"] is True
    assert body["result"]["regression_detected"] is False
    assert body["result"]["violations"] == []

    assert body["comparison"]["introduced_violations"] == []
    assert body["comparison"]["resolved_violations"] == [
        "refund_without_approval"
    ]


def test_verification_api_detects_new_violation(client) -> None:
    response = client.post(
        "/verification",
        json={
            "before": _snapshot(),
            "after": _snapshot(
                violations=["duplicate_charge"],
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["result"]["passed"] is False
    assert body["result"]["regression_detected"] is True
    assert body["result"]["violations"] == ["duplicate_charge"]

    assert body["comparison"]["introduced_violations"] == [
        "duplicate_charge"
    ]

    assert (
        body["before"]["snapshot_id"]
        == body["result"]["before_snapshot_id"]
    )
    assert (
        body["after"]["snapshot_id"]
        == body["result"]["after_snapshot_id"]
    )
    assert (
        body["comparison"]["comparison_id"]
        == body["result"]["comparison_id"]
    )


def test_verification_api_detects_baseline_change(client) -> None:
    before = _snapshot()
    after = _snapshot()

    after["baseline"]["balance"] = 900

    response = client.post(
        "/verification",
        json={
            "before": before,
            "after": after,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["result"]["passed"] is True
    assert body["comparison"]["regression_detected"] is False

    changes = body["comparison"]["changes"]

    assert any(
        change["field"] == "balance"
        and change["change_type"] == "baseline_field_changed"
        and change["before"] == 1000
        and change["after"] == 900
        for change in changes
    )


def test_verification_api_preserves_counterexample_changes(
    client,
) -> None:
    first = str(uuid4())
    second = str(uuid4())

    before = _snapshot()
    after = _snapshot()

    before["counterexample_ids"] = [first]
    after["counterexample_ids"] = [second]

    response = client.post(
        "/verification",
        json={
            "before": before,
            "after": after,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["comparison"]["added_counterexample_ids"] == [second]
    assert body["comparison"]["removed_counterexample_ids"] == [first]


def test_verification_api_rejects_unknown_fields(client) -> None:
    before = _snapshot()
    after = _snapshot()

    before["unexpected"] = True

    response = client.post(
        "/verification",
        json={
            "before": before,
            "after": after,
        },
    )

    assert response.status_code == 422
