"""Exercise the running Docker Compose stack through its public endpoints."""

from __future__ import annotations

import argparse
import json
import urllib.request
from typing import Any


def _json_request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode())


def _status(url: str) -> int:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--prometheus", default="http://localhost:9090")
    parser.add_argument("--grafana", default="http://localhost:3001")
    parser.add_argument("--minio", default="http://localhost:9000")
    args = parser.parse_args()

    live = _json_request(f"{args.api}/health/live")
    ready = _json_request(f"{args.api}/health/ready")
    prediction = _json_request(
        f"{args.api}/v1/risk-score",
        method="POST",
        payload={
            "transaction_id": "tx-docker-smoke",
            "customer_id": "customer-docker-smoke",
            "event_time": "2026-01-15T02:30:00Z",
            "amount": 1800.0,
            "currency": "PLN",
            "merchant_category": "electronics",
            "country": "PL",
            "device_trust_score": 0.12,
            "account_age_days": 12,
            "is_new_device": True,
            "velocity_1h": 9,
            "distance_km": 850.0,
            "chargeback_history": 1,
        },
    )
    targets = _json_request(f"{args.prometheus}/api/v1/targets")
    active_targets = targets["data"]["activeTargets"]
    if not any(
        target["labels"].get("job") == "sentinelflow-api" and target["health"] == "up"
        for target in active_targets
    ):
        raise RuntimeError("Prometheus is not scraping a healthy sentinelflow-api target")
    grafana = _json_request(f"{args.grafana}/api/health")

    result = {
        "api_live": live["status"],
        "api_ready": ready["status"],
        "model_version": ready["model_version"],
        "prediction_decision": prediction["decision"],
        "prediction_score": prediction["risk_score"],
        "prometheus_target": "up",
        "grafana_database": grafana["database"],
        "minio_status": _status(f"{args.minio}/minio/health/live"),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
