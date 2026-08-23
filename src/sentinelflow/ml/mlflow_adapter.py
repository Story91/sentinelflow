"""Thin MLflow integration preserving the local registry contract."""

from __future__ import annotations

from pathlib import Path
from typing import cast


def log_training_run(
    *,
    metrics: dict[str, float],
    params: dict[str, str | int | float],
    artifact_directory: Path,
    experiment_name: str = "sentinelflow-risk-scoring",
    tracking_uri: str | None = None,
) -> str:
    try:
        import mlflow
    except ImportError as exc:
        raise RuntimeError("Install sentinelflow[tracking] to use the MLflow adapter") from exc
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.log_artifacts(str(artifact_directory))
        return cast(str, run.info.run_id)
