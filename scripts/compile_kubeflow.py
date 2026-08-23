"""Compile the Kubeflow pipeline to a portable YAML specification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    from kfp import compiler

    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))
    from pipelines.kubeflow.pipeline import training_pipeline

    args.output.parent.mkdir(parents=True, exist_ok=True)
    compiler.Compiler().compile(training_pipeline, str(args.output))
    print(
        json.dumps(
            {"compiled": args.output.is_file(), "bytes": args.output.stat().st_size},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
