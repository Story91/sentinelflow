from pathlib import Path

import pytest

from sentinelflow.sagemaker import resolve_sagemaker_paths


def test_resolve_sagemaker_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    channel = tmp_path / "channel"
    model_directory = tmp_path / "model"
    monkeypatch.setenv("SM_CHANNEL_TRAIN", str(channel))
    monkeypatch.setenv("SM_MODEL_DIR", str(model_directory))
    monkeypatch.setenv("SENTINELFLOW_TRAINING_FILE", "batch/transactions.csv")

    data_path, registry_path = resolve_sagemaker_paths()

    assert data_path == channel / "batch" / "transactions.csv"
    assert registry_path == model_directory


@pytest.mark.parametrize("name", ["../transactions.csv", "/tmp/transactions.csv"])
def test_training_file_cannot_escape_channel(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    name: str,
) -> None:
    monkeypatch.setenv("SM_CHANNEL_TRAIN", str(tmp_path / "channel"))
    monkeypatch.setenv("SENTINELFLOW_TRAINING_FILE", name)

    with pytest.raises(ValueError, match="relative path"):
        resolve_sagemaker_paths()
