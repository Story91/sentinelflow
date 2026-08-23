"""Reference training pipeline used by the CLI, Airflow, and CI smoke tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from sentinelflow.data.features import build_matrix
from sentinelflow.data.validation import read_transactions
from sentinelflow.ml.evaluation import classification_metrics
from sentinelflow.ml.model import LogisticConfig, NumpyRiskModel
from sentinelflow.ml.quality_gate import assert_quality_gates
from sentinelflow.ml.registry import FileModelRegistry, RegisteredModel


def _file_fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def train_and_register(
    data_path: Path,
    registry_path: Path,
    *,
    model_name: str = "risk-scorer",
    seed: int = 42,
    test_ratio: float = 0.2,
    promote: bool = True,
    decision_threshold: float = 0.5,
    minimum_roc_auc: float = 0.65,
    minimum_recall: float = 0.25,
) -> tuple[RegisteredModel, dict[str, float]]:
    transactions, report = read_transactions(data_path, require_labels=True)
    if not report.is_healthy:
        raise ValueError(f"Input validation failed: {report.errors}")
    features, labels = build_matrix(transactions)
    assert labels is not None
    if not 0.05 <= test_ratio <= 0.5:
        raise ValueError("test_ratio must be between 0.05 and 0.5")

    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(features))
    split = int(len(indices) * (1 - test_ratio))
    train_indices, test_indices = indices[:split], indices[split:]
    model = NumpyRiskModel(LogisticConfig(seed=seed))
    model.fit(features[train_indices], labels[train_indices])
    scores = model.predict_proba(features[test_indices])
    metrics = classification_metrics(labels[test_indices], scores)
    registry = FileModelRegistry(registry_path, model_name)
    registered = registry.register(
        model,
        metrics,
        training_rows=len(train_indices),
        data_fingerprint=_file_fingerprint(data_path),
    )
    if promote:
        assert_quality_gates(
            metrics,
            minimum_roc_auc=minimum_roc_auc,
            minimum_recall=minimum_recall,
        )
        registry.promote(registered, threshold=decision_threshold)
    return registered, metrics
