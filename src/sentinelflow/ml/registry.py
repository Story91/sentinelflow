"""Filesystem model registry with explicit promotion semantics.

This is the local implementation of the same contract that can later be backed
by MLflow. A model is never overwritten: each registration gets an immutable
version directory, and promotion only updates a small champion pointer.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sentinelflow.data.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION
from sentinelflow.ml.model import NumpyRiskModel


class RegistryError(RuntimeError):
    """Raised for invalid registry state or promotion requests."""


@dataclass(frozen=True, slots=True)
class RegisteredModel:
    name: str
    version: str
    path: Path
    metrics: dict[str, float]
    metadata: dict[str, Any]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
        temporary = Path(stream.name)
    temporary.replace(path)


class FileModelRegistry:
    def __init__(self, root: Path, model_name: str = "risk-scorer") -> None:
        self.root = root
        self.model_name = model_name

    @property
    def model_root(self) -> Path:
        return self.root / self.model_name

    def register(
        self,
        model: NumpyRiskModel,
        metrics: dict[str, float],
        *,
        training_rows: int,
        data_fingerprint: str,
    ) -> RegisteredModel:
        version = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        path = self.model_root / version
        metadata: dict[str, Any] = {
            "name": self.model_name,
            "version": version,
            "registered_at": datetime.now(UTC).isoformat(),
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "training_rows": training_rows,
            "data_fingerprint": data_fingerprint,
            "metrics": metrics,
        }
        model.save(path, tuple(FEATURE_NAMES), metadata)
        metadata_path = path / "metadata.json"
        persisted_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        persisted_metadata["artifact_sha256"] = _sha256(path / "model.npz")
        _atomic_json_write(metadata_path, persisted_metadata)
        return RegisteredModel(self.model_name, version, path, metrics, persisted_metadata)

    def promote(self, registered: RegisteredModel, *, threshold: float = 0.5) -> None:
        if not (registered.path / "model.npz").exists():
            raise RegistryError(f"Model artifact does not exist: {registered.path}")
        pointer = {
            "name": registered.name,
            "version": registered.version,
            "threshold": threshold,
            "promoted_at": datetime.now(UTC).isoformat(),
        }
        _atomic_json_write(self.model_root / "champion.json", pointer)

    def champion(self) -> RegisteredModel:
        pointer_path = self.model_root / "champion.json"
        if not pointer_path.exists():
            raise RegistryError(f"No champion model found in {self.model_root}")
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        version = str(pointer.get("version", ""))
        if not version:
            raise RegistryError(f"Champion pointer has no version: {pointer_path}")
        path = self.model_root / version
        legacy_path = pointer.get("path")
        if not path.exists() and legacy_path:
            path = Path(str(legacy_path))
        metadata_path = path / "metadata.json"
        if not metadata_path.exists():
            raise RegistryError(f"Champion metadata is missing: {metadata_path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        artifact_path = path / "model.npz"
        expected_checksum = str(metadata.get("artifact_sha256", ""))
        if not expected_checksum:
            raise RegistryError(f"Champion artifact checksum is missing: {metadata_path}")
        if not artifact_path.exists() or _sha256(artifact_path) != expected_checksum:
            raise RegistryError(f"Champion artifact checksum mismatch: {artifact_path}")
        return RegisteredModel(
            name=str(pointer["name"]),
            version=str(pointer["version"]),
            path=path,
            metrics={str(k): float(v) for k, v in metadata.get("metrics", {}).items()},
            metadata=metadata,
        )

    def load_champion(self) -> tuple[NumpyRiskModel, RegisteredModel, float]:
        registered = self.champion()
        pointer = json.loads((self.model_root / "champion.json").read_text(encoding="utf-8"))
        threshold = float(pointer.get("threshold", 0.5))
        return NumpyRiskModel.load(registered.path), registered, threshold
