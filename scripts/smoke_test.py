"""Run the complete local reference path without external services."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from sentinelflow.api.service import RiskScoringService
from sentinelflow.data.generator import generate_transactions, write_transactions
from sentinelflow.ml.registry import FileModelRegistry
from sentinelflow.ml.training import train_and_register
from sentinelflow.observability.metrics import Metrics


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sentinelflow-smoke-") as raw_dir:
        root = Path(raw_dir)
        data_path = root / "transactions.csv"
        registry_path = root / "model-registry"
        transactions = generate_transactions(500, seed=42)
        write_transactions(transactions, data_path)
        registered, metrics = train_and_register(data_path, registry_path)
        model, champion, threshold = FileModelRegistry(registry_path).load_champion()
        service = RiskScoringService(model, champion, threshold, Metrics())
        prediction = service.predict(transactions[0])
        print(
            json.dumps(
                {
                    "rows": len(transactions),
                    "model_version": registered.version,
                    "roc_auc": metrics["roc_auc"],
                    "prediction": prediction.risk_score,
                    "decision": prediction.decision,
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
