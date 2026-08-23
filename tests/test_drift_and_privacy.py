from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from sentinelflow.ml.drift import (
    drift_status,
    model_performance_status,
    population_stability_index,
)
from sentinelflow.security.privacy import is_expired, pseudonymize_identifier


def test_drift_status_is_monotonic() -> None:
    reference = np.linspace(0, 1, 100)
    assert drift_status(population_stability_index(reference, reference)) == "stable"
    assert drift_status(0.12) == "warning"
    assert drift_status(0.30) == "critical"
    assert (
        model_performance_status(
            {"roc_auc": 0.8, "recall": 0.6},
            {"roc_auc": 0.73, "recall": 0.58},
        )
        == "critical"
    )
    assert (
        model_performance_status(
            {"roc_auc": 0.8, "recall": 0.6},
            {"roc_auc": 0.79, "recall": 0.59},
        )
        == "warning"
    )


def test_pseudonymization_is_stable_and_secret_dependent() -> None:
    first = pseudonymize_identifier("customer-1", "test-secret")
    assert first == pseudonymize_identifier("customer-1", "test-secret")
    assert first != pseudonymize_identifier("customer-1", "other-secret")
    with pytest.raises(ValueError):
        pseudonymize_identifier("customer-1", "change-me-locally")


def test_retention_cutoff() -> None:
    now = datetime(2026, 1, 31, tzinfo=UTC)
    assert is_expired(now - timedelta(days=91), retention_days=90, now=now)
    assert not is_expired(now - timedelta(days=10), retention_days=90, now=now)
