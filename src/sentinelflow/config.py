"""Validated configuration loaded from YAML with environment overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(ValueError):
    """Raised when project configuration is malformed or unsafe."""


def _load_yaml(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ConfigurationError(f"Expected a mapping in {path}")
    return payload


def _probability(value: object, name: str) -> float:
    parsed = float(str(value))
    if not 0 <= parsed <= 1:
        raise ConfigurationError(f"{name} must be between 0 and 1")
    return parsed


@dataclass(frozen=True, slots=True)
class AppSettings:
    environment: str = "local"
    model_registry: Path = Path("./model-registry")
    model_name: str = "risk-scorer"
    log_level: str = "INFO"
    log_file: Path | None = None

    @classmethod
    def load(cls, path: Path | None = None) -> AppSettings:
        configured_path = path
        if configured_path is None:
            configured_path = Path(os.getenv("SENTINELFLOW_CONFIG", "configs/app.yaml"))
        payload = _load_yaml(configured_path)
        logging_config = payload.get("logging", {})
        if not isinstance(logging_config, dict):
            raise ConfigurationError("logging must be a mapping")
        log_file = os.getenv("SENTINELFLOW_LOG_FILE")
        return cls(
            environment=os.getenv("SENTINELFLOW_ENV", str(payload.get("environment", "local"))),
            model_registry=Path(
                os.getenv(
                    "SENTINELFLOW_MODEL_REGISTRY",
                    str(payload.get("model_registry", "./model-registry")),
                )
            ),
            model_name=os.getenv(
                "SENTINELFLOW_MODEL_NAME", str(payload.get("model_name", "risk-scorer"))
            ),
            log_level=os.getenv(
                "SENTINELFLOW_LOG_LEVEL", str(logging_config.get("level", "INFO"))
            ).upper(),
            log_file=Path(log_file) if log_file else None,
        )


@dataclass(frozen=True, slots=True)
class TrainingPolicy:
    decision_threshold: float = 0.50
    minimum_roc_auc: float = 0.65
    minimum_recall: float = 0.25
    maximum_invalid_input_rate: float = 0.01
    psi_warning: float = 0.10
    psi_critical: float = 0.25

    @classmethod
    def load(cls, path: Path | None = None) -> TrainingPolicy:
        configured_path = path
        if configured_path is None:
            configured_path = Path(
                os.getenv("SENTINELFLOW_THRESHOLDS_CONFIG", "configs/thresholds.yaml")
            )
        payload = _load_yaml(configured_path)
        gates = payload.get("quality_gates", {})
        drift = payload.get("drift", {})
        if not isinstance(gates, dict) or not isinstance(drift, dict):
            raise ConfigurationError("quality_gates and drift must be mappings")
        policy = cls(
            decision_threshold=_probability(
                payload.get("decision_threshold", 0.50), "decision_threshold"
            ),
            minimum_roc_auc=_probability(gates.get("minimum_roc_auc", 0.65), "minimum_roc_auc"),
            minimum_recall=_probability(gates.get("minimum_recall", 0.25), "minimum_recall"),
            maximum_invalid_input_rate=_probability(
                gates.get("maximum_invalid_input_rate", 0.01),
                "maximum_invalid_input_rate",
            ),
            psi_warning=float(drift.get("psi_warning", 0.10)),
            psi_critical=float(drift.get("psi_critical", 0.25)),
        )
        if not 0 <= policy.psi_warning < policy.psi_critical:
            raise ConfigurationError("drift thresholds must satisfy 0 <= warning < critical")
        return policy
