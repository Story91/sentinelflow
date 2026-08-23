"""Data and model drift primitives used by the monitoring pipeline."""

from __future__ import annotations

import numpy as np


def population_stability_index(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Calculate PSI with shared quantile bins and safe zero handling."""
    if reference.ndim != 1 or current.ndim != 1 or not len(reference) or not len(current):
        raise ValueError("reference and current must be non-empty 1-D arrays")
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 2:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)
    ref_share = np.clip(ref_counts / len(reference), 1e-6, None)
    cur_share = np.clip(cur_counts / len(current), 1e-6, None)
    return float(np.sum((cur_share - ref_share) * np.log(cur_share / ref_share)))


def drift_status(psi: float, *, warn_at: float = 0.1, critical_at: float = 0.25) -> str:
    if psi >= critical_at:
        return "critical"
    if psi >= warn_at:
        return "warning"
    return "stable"


def model_performance_status(
    baseline: dict[str, float],
    current: dict[str, float],
    *,
    maximum_auc_drop: float = 0.05,
    maximum_recall_drop: float = 0.10,
) -> str:
    """Classify delayed-label model drift from a trusted baseline."""
    auc_drop = baseline.get("roc_auc", 0.0) - current.get("roc_auc", 0.0)
    recall_drop = baseline.get("recall", 0.0) - current.get("recall", 0.0)
    if auc_drop >= maximum_auc_drop or recall_drop >= maximum_recall_drop:
        return "critical"
    if auc_drop > 0 or recall_drop > 0:
        return "warning"
    return "stable"
