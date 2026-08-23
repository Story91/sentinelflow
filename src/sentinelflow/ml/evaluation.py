"""Dependency-light classification metrics for reproducible model gates."""

from __future__ import annotations

import numpy as np


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def roc_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    positives = labels == 1
    negatives = labels == 0
    positive_count = int(positives.sum())
    negative_count = int(negatives.sum())
    if not positive_count or not negative_count:
        return 0.5
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1, dtype=np.float64)
    positive_rank_sum = float(ranks[positives].sum())
    return (positive_rank_sum - positive_count * (positive_count + 1) / 2) / (
        positive_count * negative_count
    )


def classification_metrics(
    labels: np.ndarray, scores: np.ndarray, threshold: float = 0.5
) -> dict[str, float]:
    predictions = scores >= threshold
    positives = labels == 1
    negatives = labels == 0
    true_positive = float(np.sum(predictions & positives))
    false_positive = float(np.sum(predictions & negatives))
    false_negative = float(np.sum(~predictions & positives))
    true_negative = float(np.sum(~predictions & negatives))
    precision = _safe_div(true_positive, true_positive + false_positive)
    recall = _safe_div(true_positive, true_positive + false_negative)
    accuracy = _safe_div(true_positive + true_negative, len(labels))
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc(labels, scores),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "false_negative": false_negative,
    }
