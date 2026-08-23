from pathlib import Path

import yaml

from sentinelflow.data.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION


def test_documented_feature_contract_matches_runtime_schema() -> None:
    project_root = Path(__file__).resolve().parents[1]
    payload = yaml.safe_load(
        (project_root / "configs" / "feature_schema.yaml").read_text(encoding="utf-8")
    )
    configured_names = tuple(feature["name"] for feature in payload["features"])
    assert payload["schema_version"] == FEATURE_SCHEMA_VERSION
    assert configured_names == FEATURE_NAMES
