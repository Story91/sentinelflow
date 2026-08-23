"""Airflow DAG for scheduled validation, training, evaluation, and promotion."""

from datetime import datetime, timedelta

from airflow.decorators import dag, task


@dag(
    dag_id="sentinelflow_training",
    schedule="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"owner": "ml-platform", "retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["mlops", "sentinelflow"],
)
def sentinelflow_training():
    @task
    def validate_input() -> str:
        from pathlib import Path

        from sentinelflow.data.validation import read_transactions

        path = Path("/opt/sentinelflow/data/raw/transactions.csv")
        _, report = read_transactions(path, require_labels=True)
        if not report.is_healthy:
            raise ValueError(f"Input data quality failed: {report.errors}")
        return str(path)

    @task
    def train(path: str) -> dict[str, str | float]:
        import os
        from pathlib import Path

        from sentinelflow.config import TrainingPolicy
        from sentinelflow.ml.quality_gate import assert_quality_gates
        from sentinelflow.ml.training import train_and_register

        policy = TrainingPolicy.load(
            Path(
                os.getenv(
                    "SENTINELFLOW_THRESHOLDS_CONFIG",
                    "/opt/sentinelflow/configs/thresholds.yaml",
                )
            )
        )
        registered, metrics = train_and_register(
            Path(path), Path("/opt/sentinelflow/model-registry"), promote=False
        )
        assert_quality_gates(
            metrics,
            minimum_roc_auc=policy.minimum_roc_auc,
            minimum_recall=policy.minimum_recall,
        )
        return {
            "candidate_path": str(registered.path),
            "decision_threshold": policy.decision_threshold,
        }

    @task
    def promote(candidate_payload: dict[str, str | float]) -> None:
        import json
        from pathlib import Path

        from sentinelflow.ml.registry import FileModelRegistry, RegisteredModel

        path = Path(str(candidate_payload["candidate_path"]))
        decision_threshold = float(candidate_payload["decision_threshold"])
        metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        registered_candidate = RegisteredModel(
            name=metadata["name"],
            version=metadata["version"],
            path=path,
            metrics=metadata["metrics"],
            metadata=metadata,
        )
        FileModelRegistry(Path("/opt/sentinelflow/model-registry"), metadata["name"]).promote(
            registered_candidate,
            threshold=decision_threshold,
        )

    promote(train(validate_input()))


sentinelflow_training()
