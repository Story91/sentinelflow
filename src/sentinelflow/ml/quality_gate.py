"""Promotion gates for automated training pipelines."""

from __future__ import annotations


class QualityGateError(RuntimeError):
    """Raised when a candidate model must not be promoted."""


def assert_quality_gates(
    metrics: dict[str, float],
    *,
    minimum_roc_auc: float = 0.65,
    minimum_recall: float = 0.25,
) -> None:
    failures: list[str] = []
    if metrics.get("roc_auc", 0.0) < minimum_roc_auc:
        failures.append(f"roc_auc={metrics.get('roc_auc', 0.0):.4f} < {minimum_roc_auc:.4f}")
    if metrics.get("recall", 0.0) < minimum_recall:
        failures.append(f"recall={metrics.get('recall', 0.0):.4f} < {minimum_recall:.4f}")
    if failures:
        raise QualityGateError("; ".join(failures))
