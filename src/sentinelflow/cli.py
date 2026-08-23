"""Command-line entry point for the local reference workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentinelflow.config import TrainingPolicy
from sentinelflow.data.generator import generate_transactions, write_transactions
from sentinelflow.data.validation import read_transactions
from sentinelflow.ml.drift_report import build_drift_report
from sentinelflow.ml.mlflow_adapter import log_training_run
from sentinelflow.ml.training import train_and_register


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sentinelflow")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="generate deterministic synthetic data")
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument("--rows", type=int, default=5_000)
    generate.add_argument("--seed", type=int, default=42)

    train = commands.add_parser("train", help="train, register, and promote a model")
    train.add_argument("--data", type=Path, required=True)
    train.add_argument("--registry", type=Path, default=Path("./model-registry"))
    train.add_argument("--model-name", default="risk-scorer")
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--no-promote", action="store_true")
    train.add_argument("--thresholds-config", type=Path)
    train.add_argument("--mlflow-tracking-uri")
    train.add_argument("--mlflow-experiment", default="sentinelflow-risk-scoring")

    inspect = commands.add_parser("inspect", help="inspect a CSV validation report")
    inspect.add_argument("--data", type=Path, required=True)
    inspect.add_argument("--require-labels", action="store_true")

    monitor = commands.add_parser("monitor", help="compare reference and current data drift")
    monitor.add_argument("--reference", type=Path, required=True)
    monitor.add_argument("--current", type=Path, required=True)
    monitor.add_argument("--output", type=Path)
    monitor.add_argument("--thresholds-config", type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "generate":
        count = write_transactions(generate_transactions(args.rows, args.seed), args.output)
        print(json.dumps({"written_rows": count, "output": str(args.output)}))
        return 0
    if args.command == "train":
        policy = TrainingPolicy.load(args.thresholds_config)
        registered, metrics = train_and_register(
            args.data,
            args.registry,
            model_name=args.model_name,
            seed=args.seed,
            promote=not args.no_promote,
            decision_threshold=policy.decision_threshold,
            minimum_roc_auc=policy.minimum_roc_auc,
            minimum_recall=policy.minimum_recall,
        )
        if args.mlflow_tracking_uri:
            run_id = log_training_run(
                metrics=metrics,
                params={"model_name": args.model_name, "seed": args.seed},
                artifact_directory=registered.path,
                experiment_name=args.mlflow_experiment,
                tracking_uri=args.mlflow_tracking_uri,
            )
        else:
            run_id = None
        print(
            json.dumps(
                {
                    "model_version": registered.version,
                    "metrics": metrics,
                    "mlflow_run_id": run_id,
                },
                indent=2,
            )
        )
        return 0
    if args.command == "inspect":
        _, report = read_transactions(args.data, require_labels=args.require_labels)
        print(
            json.dumps(
                {
                    "total_rows": report.total_rows,
                    "valid_rows": report.valid_rows,
                    "invalid_rows": report.invalid_rows,
                    "errors": report.errors,
                },
                indent=2,
            )
        )
        return 0 if report.is_healthy else 2
    if args.command == "monitor":
        policy = TrainingPolicy.load(args.thresholds_config)
        reference, reference_report = read_transactions(args.reference)
        current, current_report = read_transactions(args.current)
        if not reference_report.is_healthy or not current_report.is_healthy:
            print(
                json.dumps(
                    {
                        "error": "input validation failed",
                        "reference": reference_report.errors,
                        "current": current_report.errors,
                    },
                    indent=2,
                )
            )
            return 2
        drift_report = build_drift_report(
            reference,
            current,
            warn_at=policy.psi_warning,
            critical_at=policy.psi_critical,
        )
        rendered = json.dumps(drift_report, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered)
        return 2 if drift_report["overall_status"] == "critical" else 0
    raise AssertionError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
