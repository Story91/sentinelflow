"""Optional framework adapters used for comparison experiments.

Each adapter is deliberately isolated. The production contract is the model
metadata and prediction interface, not a hard dependency on every framework in
the job description.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def fit_scikit_learn(features: np.ndarray, labels: np.ndarray) -> Any:
    try:
        from sklearn.linear_model import LogisticRegression
    except ImportError as exc:
        raise RuntimeError("Install sentinelflow[ml] to use the Scikit-learn adapter") from exc
    return LogisticRegression(max_iter=500, class_weight="balanced", random_state=42).fit(
        features, labels
    )


def fit_xgboost(features: np.ndarray, labels: np.ndarray) -> Any:
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError("Install sentinelflow[ml] to use the XGBoost adapter") from exc
    positive = max(float(labels.sum()), 1.0)
    negative = max(float((labels == 0).sum()), 1.0)
    return XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
        scale_pos_weight=negative / positive,
    ).fit(features, labels)


def fit_pytorch(features: np.ndarray, labels: np.ndarray, epochs: int = 50) -> Any:
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise RuntimeError(
            "Install sentinelflow[ml] with PyTorch separately to use this adapter"
        ) from exc

    torch.manual_seed(42)
    model = nn.Sequential(nn.Linear(features.shape[1], 32), nn.ReLU(), nn.Linear(32, 1))
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01, weight_decay=0.001)
    loss_fn = nn.BCEWithLogitsLoss()
    x = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(labels.reshape(-1, 1), dtype=torch.float32)
    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        optimizer.step()
    return model


def fit_tensorflow_keras(features: np.ndarray, labels: np.ndarray, epochs: int = 12) -> Any:
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError(
            "Install sentinelflow[ml] with TensorFlow separately to use this adapter"
        ) from exc

    tf.keras.utils.set_random_seed(42)
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(features.shape[1],)),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(0.01), loss="binary_crossentropy", metrics=["AUC"]
    )
    model.fit(features, labels, epochs=epochs, batch_size=64, verbose=0)
    return model
