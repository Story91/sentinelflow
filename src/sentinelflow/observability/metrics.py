"""Prometheus metrics with bounded-cardinality labels."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest


class Metrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.predictions = Counter(
            "sentinelflow_predictions_total",
            "Risk predictions returned by the model.",
            ("decision", "model_version"),
            registry=self.registry,
        )
        self.prediction_latency = Histogram(
            "sentinelflow_prediction_latency_seconds",
            "Time spent creating a risk prediction.",
            ("model_version",),
            registry=self.registry,
        )
        self.http_requests = Counter(
            "sentinelflow_http_requests_total",
            "HTTP responses returned by the API.",
            ("method", "path", "status_code"),
            registry=self.registry,
        )
        self.http_latency = Histogram(
            "sentinelflow_http_request_duration_seconds",
            "End-to-end HTTP request duration.",
            ("method", "path"),
            registry=self.registry,
        )
        self.model_ready = Gauge(
            "sentinelflow_model_ready",
            "Whether the serving process has loaded a champion model.",
            registry=self.registry,
        )

    def record_prediction(self, decision: str, model_version: str, duration: float) -> None:
        self.predictions.labels(decision=decision, model_version=model_version).inc()
        self.prediction_latency.labels(model_version=model_version).observe(duration)

    def record_http(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration: float,
    ) -> None:
        self.http_requests.labels(
            method=method,
            path=path,
            status_code=str(status_code),
        ).inc()
        self.http_latency.labels(method=method, path=path).observe(duration)

    def set_model_ready(self, ready: bool) -> None:
        self.model_ready.set(1 if ready else 0)

    def render_prometheus(self) -> str:
        return generate_latest(self.registry).decode("utf-8")
