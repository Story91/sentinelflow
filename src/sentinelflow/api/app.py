"""FastAPI application factory.

Run with:
    uvicorn sentinelflow.api.app:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.base import RequestResponseEndpoint

from sentinelflow.api.service import RiskScoringService
from sentinelflow.config import AppSettings
from sentinelflow.domain.schemas import DomainValidationError, Transaction
from sentinelflow.ml.registry import FileModelRegistry, RegistryError
from sentinelflow.observability.logging import configure_logging
from sentinelflow.observability.metrics import Metrics


class TransactionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=1, max_length=128)
    customer_id: str = Field(min_length=1, max_length=128)
    event_time: str
    amount: float = Field(gt=0, le=1_000_000)
    currency: str
    merchant_category: str
    country: str
    device_trust_score: float = Field(ge=0, le=1)
    account_age_days: int = Field(ge=0)
    is_new_device: bool
    velocity_1h: int = Field(ge=0)
    distance_km: float = Field(ge=0)
    chargeback_history: int = Field(ge=0)


def create_app(registry_path: Path | None = None, model_name: str | None = None) -> FastAPI:
    app = FastAPI(title="SentinelFlow Risk API", version="0.1.0")
    metrics = Metrics()
    settings = AppSettings.load()
    logger = configure_logging(settings.log_level, settings.log_file)
    configured_registry = registry_path or settings.model_registry
    configured_name = model_name or settings.model_name
    service: RiskScoringService | None = None

    try:
        model, registered, threshold = FileModelRegistry(
            configured_registry, configured_name
        ).load_champion()
        service = RiskScoringService(model, registered, threshold, metrics)
        metrics.set_model_ready(True)
    except RegistryError:
        # The container can start before the first training run. Readiness remains false.
        service = None
        metrics.set_model_ready(False)

    @app.middleware("http")
    async def observe_http(
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        started = perf_counter()
        response_status = 500
        try:
            response = await call_next(request)
            response_status = response.status_code
            return response
        except Exception:
            logger.exception(
                "unhandled request failure",
                extra={"status_code": response_status},
            )
            raise
        finally:
            duration = perf_counter() - started
            metrics.record_http(
                method=request.method,
                path=request.url.path,
                status_code=response_status,
                duration=duration,
            )
            logger.info(
                "http request completed",
                extra={
                    "status_code": response_status,
                    "duration_ms": round(duration * 1000, 3),
                },
            )

    @app.get("/health/live")
    def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready")
    def readiness() -> dict[str, str]:
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="model unavailable"
            )
        return {"status": "ready", "model_version": service.registered.version}

    @app.get("/metrics")
    def prometheus_metrics() -> Response:
        return Response(metrics.render_prometheus(), media_type="text/plain; version=0.0.4")

    @app.post("/v1/risk-score")
    def risk_score(request: TransactionRequest) -> dict[str, object]:
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="model unavailable"
            )
        try:
            prediction = service.predict(Transaction.from_mapping(request.model_dump()))
        except (DomainValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        logger.info(
            "risk prediction completed",
            extra={
                "request_id": prediction.request_id,
                "model_name": prediction.model_name,
                "model_version": prediction.model_version,
                "decision": prediction.decision,
            },
        )
        return {
            "transaction_id": prediction.transaction_id,
            "risk_score": prediction.risk_score,
            "decision": prediction.decision,
            "model_name": prediction.model_name,
            "model_version": prediction.model_version,
            "request_id": prediction.request_id,
        }

    return app


app = create_app()
