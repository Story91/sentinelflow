import numpy as np

from sentinelflow.data.features import build_matrix
from sentinelflow.data.generator import generate_transactions
from sentinelflow.ml.evaluation import classification_metrics
from sentinelflow.ml.model import NumpyRiskModel


def test_model_trains_predicts_and_persists(tmp_path) -> None:
    transactions = generate_transactions(250, seed=42)
    features, labels = build_matrix(transactions)
    assert labels is not None
    model = NumpyRiskModel()
    model.fit(features, labels)
    scores = model.predict_proba(features)
    assert scores.shape == (250,)
    assert np.all((scores >= 0) & (scores <= 1))
    metrics = classification_metrics(labels, scores)
    assert 0 <= metrics["roc_auc"] <= 1

    model.save(tmp_path / "model", tuple(f"feature_{i}" for i in range(features.shape[1])), {})
    loaded = NumpyRiskModel.load(tmp_path / "model")
    np.testing.assert_allclose(scores, loaded.predict_proba(features))
