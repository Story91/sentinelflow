"""Airflow DAG that produces a feature-level drift report."""

import os
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task


@dag(
    dag_id="sentinelflow_drift_monitor",
    schedule="0 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"owner": "ml-platform", "retries": 1},
    tags=["mlops", "monitoring", "sentinelflow"],
)
def sentinelflow_drift_monitor():
    @task
    def monitor() -> str:
        import json

        from sentinelflow.config import TrainingPolicy
        from sentinelflow.data.validation import read_transactions
        from sentinelflow.ml.drift_report import build_drift_report

        reference_path = Path(
            os.getenv(
                "SENTINELFLOW_REFERENCE_DATA",
                "/opt/sentinelflow/data/reference/transactions.csv",
            )
        )
        current_path = Path(
            os.getenv(
                "SENTINELFLOW_CURRENT_DATA",
                "/opt/sentinelflow/data/current/transactions.csv",
            )
        )
        output_path = Path(
            os.getenv(
                "SENTINELFLOW_DRIFT_REPORT",
                "/opt/sentinelflow/data/reports/drift.json",
            )
        )
        policy = TrainingPolicy.load(
            Path(
                os.getenv(
                    "SENTINELFLOW_THRESHOLDS_CONFIG",
                    "/opt/sentinelflow/configs/thresholds.yaml",
                )
            )
        )
        reference, reference_validation = read_transactions(reference_path)
        current, current_validation = read_transactions(current_path)
        if not reference_validation.is_healthy or not current_validation.is_healthy:
            raise ValueError(
                f"Drift input validation failed: "
                f"{reference_validation.errors + current_validation.errors}"
            )
        report = build_drift_report(
            reference,
            current,
            warn_at=policy.psi_warning,
            critical_at=policy.psi_critical,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if report["overall_status"] == "critical":
            raise ValueError(f"Critical drift detected; report={output_path}")
        return str(output_path)

    monitor()


sentinelflow_drift_monitor()
