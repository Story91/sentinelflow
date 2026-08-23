"""Small deterministic logistic model used by the local reference path.

The model is intentionally implemented with NumPy so the complete happy path
can run in a clean environment. The repository also contains adapters for
Scikit-learn, XGBoost, PyTorch, and TensorFlow/Keras for framework-specific
experiments.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return np.asarray(1 / (1 + np.exp(-np.clip(values, -30, 30))), dtype=np.float64)


@dataclass(slots=True)
class LogisticConfig:
    learning_rate: float = 0.08
    epochs: int = 600
    l2: float = 0.002
    seed: int = 42


class NumpyRiskModel:
    """Binary classifier with persisted preprocessing statistics."""

    algorithm = "numpy-logistic-regression"

    def __init__(self, config: LogisticConfig | None = None) -> None:
        self.config = config or LogisticConfig()
        self.weights: np.ndarray | None = None
        self.bias = 0.0
        self.mean: np.ndarray | None = None
        self.scale: np.ndarray | None = None

    @property
    def is_fitted(self) -> bool:
        return self.weights is not None and self.mean is not None and self.scale is not None

    def fit(self, features: np.ndarray, labels: np.ndarray) -> NumpyRiskModel:
        if features.ndim != 2 or labels.ndim != 1 or len(features) != len(labels):
            raise ValueError("features must be 2-D and labels must match its row count")
        if len(np.unique(labels)) < 2:
            raise ValueError("Training requires both positive and negative labels")
        if not np.all(np.isin(labels, [0, 1])):
            raise ValueError("labels must contain only 0 and 1")

        mean = features.mean(axis=0)
        scale = features.std(axis=0)
        scale = np.where(scale < 1e-8, 1.0, scale)
        self.mean = mean
        self.scale = scale
        x = (features - mean) / scale
        rng = np.random.default_rng(self.config.seed)
        weights: np.ndarray = np.asarray(
            rng.normal(0, 0.01, size=features.shape[1]),
            dtype=np.float64,
        )
        bias: float = 0.0

        for _ in range(self.config.epochs):
            probabilities = _sigmoid(x @ weights + bias)
            error = probabilities - labels
            gradient = (x.T @ error) / len(x) + self.config.l2 * weights
            weights -= self.config.learning_rate * gradient
            bias -= self.config.learning_rate * float(error.mean())
        self.weights = weights
        self.bias = bias
        return self

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted")
        assert self.weights is not None and self.mean is not None and self.scale is not None
        x = (features - self.mean) / self.scale
        return _sigmoid(x @ self.weights + self.bias)

    def save(
        self, directory: Path, feature_names: tuple[str, ...], metadata: dict[str, object]
    ) -> None:
        if not self.is_fitted:
            raise RuntimeError("Cannot save an unfitted model")
        assert self.weights is not None and self.mean is not None and self.scale is not None
        directory.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            directory / "model.npz",
            weights=self.weights,
            bias=np.asarray([self.bias]),
            mean=self.mean,
            scale=self.scale,
        )
        payload = {
            **metadata,
            "algorithm": self.algorithm,
            "feature_names": list(feature_names),
            "feature_count": len(feature_names),
            "model_format": "numpy-npz-v1",
        }
        (directory / "metadata.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )

    @classmethod
    def load(cls, directory: Path) -> NumpyRiskModel:
        model = cls()
        with np.load(directory / "model.npz", allow_pickle=False) as arrays:
            model.weights = arrays["weights"]
            model.bias = float(arrays["bias"][0])
            model.mean = arrays["mean"]
            model.scale = arrays["scale"]
        return model
