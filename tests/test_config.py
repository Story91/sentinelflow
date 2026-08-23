from pathlib import Path

import pytest

from sentinelflow.config import ConfigurationError, TrainingPolicy


def test_training_policy_loads_repository_config() -> None:
    project_root = Path(__file__).resolve().parents[1]
    policy = TrainingPolicy.load(project_root / "configs" / "thresholds.yaml")
    assert policy.decision_threshold == 0.5
    assert policy.minimum_roc_auc == 0.65
    assert policy.psi_warning < policy.psi_critical


def test_training_policy_rejects_inverted_drift_thresholds(tmp_path: Path) -> None:
    config = tmp_path / "thresholds.yaml"
    config.write_text(
        "drift:\n  psi_warning: 0.4\n  psi_critical: 0.2\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="warning < critical"):
        TrainingPolicy.load(config)
