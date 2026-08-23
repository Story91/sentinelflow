"""Application service independent from the HTTP framework."""

from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from sentinelflow.data.features import build_matrix
from sentinelflow.domain.schemas import RiskPrediction, Transaction
from sentinelflow.ml.model import NumpyRiskModel
from sentinelflow.ml.registry import RegisteredModel
from sentinelflow.observability.metrics import Metrics


class RiskScoringService:
    def __init__(
        self, model: NumpyRiskModel, registered: RegisteredModel, threshold: float, metrics: Metrics
    ) -> None:
        self.model = model
        self.registered = registered
        self.threshold = threshold
        self.metrics = metrics

    def predict(self, transaction: Transaction) -> RiskPrediction:
        started = perf_counter()
        features, _ = build_matrix([transaction], require_labels=False)
        score = float(self.model.predict_proba(features)[0])
        decision = "review" if score >= self.threshold else "approve"
        self.metrics.record_prediction(
            decision,
            self.registered.version,
            perf_counter() - started,
        )
        return RiskPrediction(
            transaction_id=transaction.transaction_id,
            risk_score=round(score, 6),
            decision=decision,
            model_name=self.registered.name,
            model_version=self.registered.version,
            request_id=f"req_{uuid4().hex}",
        )
