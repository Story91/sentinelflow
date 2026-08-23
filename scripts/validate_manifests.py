"""Parse repository YAML and JSON files to catch malformed manifests in CI."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "data",
    "logs",
    "mlruns",
    "model-registry",
}


def main() -> int:
    yaml_count = 0
    json_count = 0
    for path in sorted(PROJECT_ROOT.rglob("*")):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in {".yaml", ".yml"}:
            list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
            yaml_count += 1
        elif path.suffix.lower() == ".json":
            json.loads(path.read_text(encoding="utf-8"))
            json_count += 1
    print(json.dumps({"yaml_files": yaml_count, "json_files": json_count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
