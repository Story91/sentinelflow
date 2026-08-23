import numpy as np

from sentinelflow.data.features import FEATURE_NAMES, build_matrix, vectorize
from sentinelflow.data.generator import generate_transactions


def test_feature_schema_is_stable() -> None:
    transactions = generate_transactions(5, seed=7)
    features, labels = build_matrix(transactions)
    assert features.shape == (5, len(FEATURE_NAMES))
    assert labels is not None
    assert labels.shape == (5,)
    assert np.isfinite(features).all()


def test_online_and_offline_vectorization_share_shape() -> None:
    transaction = generate_transactions(2, seed=11)[0]
    online, _ = build_matrix([transaction], require_labels=False)
    assert online.shape == (1, len(vectorize(transaction)))
