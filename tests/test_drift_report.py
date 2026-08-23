from dataclasses import replace

from sentinelflow.data.generator import generate_transactions
from sentinelflow.ml.drift_report import build_drift_report


def test_drift_report_detects_large_amount_shift() -> None:
    reference = generate_transactions(300, seed=10)
    stable = build_drift_report(reference, list(reference))
    assert stable["overall_status"] == "stable"

    shifted = [replace(event, amount=event.amount * 50) for event in reference]
    drifted = build_drift_report(reference, shifted)
    assert drifted["overall_status"] == "critical"
    amount = next(item for item in drifted["features"] if item["name"] == "log_amount")
    assert amount["status"] == "critical"
