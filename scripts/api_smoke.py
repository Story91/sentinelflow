"""Start the real FastAPI application briefly and exercise its HTTP contract."""

from __future__ import annotations

import json
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import uvicorn

from sentinelflow.api.app import create_app
from sentinelflow.data.generator import generate_transactions, write_transactions
from sentinelflow.ml.training import train_and_register


def _request(
    url: str, *, method: str = "GET", payload: dict[str, object] | None = None
) -> dict[str, object]:
    body = None
    headers: dict[str, str] = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sentinelflow-api-smoke-") as raw_dir:
        root = Path(raw_dir)
        transactions = generate_transactions(500, seed=42)
        data_path = root / "transactions.csv"
        registry_path = root / "model-registry"
        write_transactions(transactions, data_path)
        train_and_register(data_path, registry_path)

        config = uvicorn.Config(
            create_app(registry_path), host="127.0.0.1", port=8765, log_level="error"
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        try:
            for _ in range(30):
                try:
                    _request("http://127.0.0.1:8765/health/live")
                    break
                except (ConnectionError, urllib.error.URLError):
                    time.sleep(0.1)
            payload = transactions[0].to_mapping()
            payload.pop("is_fraud", None)
            print(
                json.dumps(
                    _request(
                        "http://127.0.0.1:8765/v1/risk-score",
                        method="POST",
                        payload=payload,
                    ),
                    indent=2,
                )
            )
        finally:
            server.should_exit = True
            thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
