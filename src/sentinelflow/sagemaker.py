"""SageMaker training-container adapter for the canonical training workflow."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from sentinelflow.config import TrainingPolicy
from sentinelflow.ml.training import train_and_register


def _path_inside(directory: Path, relative_name: str) -> Path:
    candidate_name = Path(relative_name)
    if candidate_name.is_absolute() or ".." in candidate_name.parts:
        raise ValueError("SENTINELFLOW_TRAINING_FILE must be a relative path without '..'")
    root = directory.resolve()
    candidate = (root / candidate_name).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("training data must remain inside SM_CHANNEL_TRAIN")
    return candidate


def resolve_sagemaker_paths() -> tuple[Path, Path]:
    """Resolve SageMaker's documented channel and model directories."""

    channel = Path(os.getenv("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train"))
    training_file = os.getenv("SENTINELFLOW_TRAINING_FILE", "transactions.csv")
    model_directory = Path(os.getenv("SM_MODEL_DIR", "/opt/ml/model"))
    return _path_inside(channel, training_file), model_directory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sentinelflow-sagemaker")
    parser.add_argument("command", choices=("train",), help="SageMaker container command")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run training using paths injected by SageMaker."""

    _build_parser().parse_args(argv)
    data_path, registry_path = resolve_sagemaker_paths()
    policy = TrainingPolicy.load()
    model_name = os.getenv("SENTINELFLOW_MODEL_NAME", "risk-scorer")
    seed = int(os.getenv("SENTINELFLOW_SEED", "42"))
    registered, metrics = train_and_register(
        data_path,
        registry_path,
        model_name=model_name,
        seed=seed,
        decision_threshold=policy.decision_threshold,
        minimum_roc_auc=policy.minimum_roc_auc,
        minimum_recall=policy.minimum_recall,
    )
    print(
        json.dumps(
            {
                "model_version": registered.version,
                "model_directory": str(registry_path),
                "metrics": metrics,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
