import pytest

from sentinelflow.ml.quality_gate import QualityGateError, assert_quality_gates


def test_quality_gate_accepts_candidate() -> None:
    assert_quality_gates({"roc_auc": 0.8, "recall": 0.4})


def test_quality_gate_rejects_candidate() -> None:
    with pytest.raises(QualityGateError, match="roc_auc"):
        assert_quality_gates({"roc_auc": 0.5, "recall": 0.4})
