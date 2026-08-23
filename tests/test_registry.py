import json
import shutil

import pytest

from sentinelflow.data.features import build_matrix
from sentinelflow.data.generator import generate_transactions, write_transactions
from sentinelflow.ml.evaluation import classification_metrics
from sentinelflow.ml.model import NumpyRiskModel
from sentinelflow.ml.registry import FileModelRegistry, RegistryError


def test_registry_promotes_immutable_model(tmp_path) -> None:
    data_path = tmp_path / "transactions.csv"
    write_transactions(generate_transactions(100, seed=2), data_path)
    events = generate_transactions(100, seed=2)
    features, labels = build_matrix(events)
    assert labels is not None
    model = NumpyRiskModel().fit(features, labels)
    registered = FileModelRegistry(tmp_path / "registry").register(
        model,
        classification_metrics(labels, model.predict_proba(features)),
        training_rows=100,
        data_fingerprint="abc",
    )
    registry = FileModelRegistry(tmp_path / "registry")
    registry.promote(registered)
    assert len(registered.metadata["artifact_sha256"]) == 64
    pointer = json.loads((tmp_path / "registry" / "risk-scorer" / "champion.json").read_text())
    assert "path" not in pointer
    loaded, champion, threshold = registry.load_champion()
    assert champion.version == registered.version
    assert threshold == 0.5
    assert loaded.predict_proba(features).shape == (100,)

    moved_root = tmp_path / "moved-registry"
    shutil.copytree(tmp_path / "registry", moved_root)
    moved_model, moved_champion, _ = FileModelRegistry(moved_root).load_champion()
    assert moved_champion.version == registered.version
    assert moved_model.predict_proba(features).shape == (100,)

    with (moved_champion.path / "model.npz").open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(RegistryError, match="checksum mismatch"):
        FileModelRegistry(moved_root).load_champion()
