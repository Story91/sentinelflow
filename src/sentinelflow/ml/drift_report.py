"""Feature-level data drift reports for scheduled monitoring jobs."""

from __future__ import annotations

from typing import Any

from sentinelflow.data.features import FEATURE_NAMES, build_matrix
from sentinelflow.domain.schemas import Transaction
from sentinelflow.ml.drift import drift_status, population_stability_index


def build_drift_report(
    reference: list[Transaction],
    current: list[Transaction],
    *,
    warn_at: float = 0.10,
    critical_at: float = 0.25,
) -> dict[str, Any]:
    reference_matrix, _ = build_matrix(reference, require_labels=False)
    current_matrix, _ = build_matrix(current, require_labels=False)
    features: list[dict[str, float | str]] = []
    severities = {"stable": 0, "warning": 1, "critical": 2}
    overall = "stable"
    for index, name in enumerate(FEATURE_NAMES):
        psi = population_stability_index(reference_matrix[:, index], current_matrix[:, index])
        status = drift_status(psi, warn_at=warn_at, critical_at=critical_at)
        if severities[status] > severities[overall]:
            overall = status
        features.append({"name": name, "psi": round(psi, 6), "status": status})
    return {
        "reference_rows": len(reference),
        "current_rows": len(current),
        "overall_status": overall,
        "features": features,
    }
