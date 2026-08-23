"""Canonical domain schemas.

The project deliberately keeps the domain layer independent from FastAPI, Spark,
Kafka, and model frameworks. This makes the rules testable and reusable by every
ingestion path.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

SUPPORTED_COUNTRIES = frozenset({"PL", "DE", "FR", "GB", "US", "ES", "IT"})
SUPPORTED_CURRENCIES = frozenset({"PLN", "EUR", "GBP", "USD"})
SUPPORTED_MERCHANT_CATEGORIES = frozenset(
    {"grocery", "electronics", "travel", "gaming", "fashion", "utilities"}
)


class DomainValidationError(ValueError):
    """Raised when an input cannot be represented by a valid domain object."""


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes"}:
        return True
    if normalized in {"0", "false", "f", "no"}:
        return False
    raise DomainValidationError(f"Invalid boolean value: {value!r}")


def _parse_event_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise DomainValidationError(f"Invalid event_time: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class Transaction:
    """Minimal event needed for risk scoring.

    Customer identifiers in the demo are synthetic. In a real system the value
    entering this boundary would already be tokenized or pseudonymized.
    """

    transaction_id: str
    customer_id: str
    event_time: datetime
    amount: float
    currency: str
    merchant_category: str
    country: str
    device_trust_score: float
    account_age_days: int
    is_new_device: bool
    velocity_1h: int
    distance_km: float
    chargeback_history: int
    is_fraud: int | None = None

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> Transaction:
        required = {
            "transaction_id",
            "customer_id",
            "event_time",
            "amount",
            "currency",
            "merchant_category",
            "country",
            "device_trust_score",
            "account_age_days",
            "is_new_device",
            "velocity_1h",
            "distance_km",
            "chargeback_history",
        }
        missing = sorted(required - set(row))
        if missing:
            raise DomainValidationError(f"Missing fields: {', '.join(missing)}")

        label = row.get("is_fraud")
        parsed_label = None if label in (None, "", "null") else int(str(label))
        transaction = cls(
            transaction_id=str(row["transaction_id"]).strip(),
            customer_id=str(row["customer_id"]).strip(),
            event_time=_parse_event_time(row["event_time"]),
            amount=float(row["amount"]),
            currency=str(row["currency"]).strip().upper(),
            merchant_category=str(row["merchant_category"]).strip().lower(),
            country=str(row["country"]).strip().upper(),
            device_trust_score=float(row["device_trust_score"]),
            account_age_days=int(row["account_age_days"]),
            is_new_device=_parse_bool(row["is_new_device"]),
            velocity_1h=int(row["velocity_1h"]),
            distance_km=float(row["distance_km"]),
            chargeback_history=int(row["chargeback_history"]),
            is_fraud=parsed_label,
        )
        transaction.validate()
        return transaction

    def validate(self) -> None:
        errors: list[str] = []
        if not self.transaction_id:
            errors.append("transaction_id must not be empty")
        if not self.customer_id:
            errors.append("customer_id must not be empty")
        if not 0 < self.amount <= 1_000_000:
            errors.append("amount must be in (0, 1_000_000]")
        if self.currency not in SUPPORTED_CURRENCIES:
            errors.append(f"unsupported currency: {self.currency}")
        if self.merchant_category not in SUPPORTED_MERCHANT_CATEGORIES:
            errors.append(f"unsupported merchant_category: {self.merchant_category}")
        if self.country not in SUPPORTED_COUNTRIES:
            errors.append(f"unsupported country: {self.country}")
        if not 0 <= self.device_trust_score <= 1:
            errors.append("device_trust_score must be between 0 and 1")
        if self.account_age_days < 0:
            errors.append("account_age_days must be non-negative")
        if self.velocity_1h < 0:
            errors.append("velocity_1h must be non-negative")
        if self.distance_km < 0:
            errors.append("distance_km must be non-negative")
        if self.chargeback_history < 0:
            errors.append("chargeback_history must be non-negative")
        if self.is_fraud not in (None, 0, 1):
            errors.append("is_fraud must be 0, 1, or null")
        if errors:
            raise DomainValidationError("; ".join(errors))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "customer_id": self.customer_id,
            "event_time": self.event_time.isoformat(),
            "amount": self.amount,
            "currency": self.currency,
            "merchant_category": self.merchant_category,
            "country": self.country,
            "device_trust_score": self.device_trust_score,
            "account_age_days": self.account_age_days,
            "is_new_device": int(self.is_new_device),
            "velocity_1h": self.velocity_1h,
            "distance_km": self.distance_km,
            "chargeback_history": self.chargeback_history,
            "is_fraud": self.is_fraud,
        }


@dataclass(frozen=True, slots=True)
class RiskPrediction:
    """Stable response contract returned by every serving implementation."""

    transaction_id: str
    risk_score: float
    decision: str
    model_name: str
    model_version: str
    request_id: str
