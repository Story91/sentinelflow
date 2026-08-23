"""Versioned feature transformation shared by training and serving."""

from __future__ import annotations

import math

import numpy as np

from sentinelflow.domain.schemas import Transaction

FEATURE_SCHEMA_VERSION = "transaction-risk-v1"
MERCHANT_CATEGORIES = ("grocery", "electronics", "travel", "gaming", "fashion", "utilities")
COUNTRIES = ("PL", "DE", "FR", "GB", "US", "ES", "IT")
CURRENCIES = ("PLN", "EUR", "GBP", "USD")

FEATURE_NAMES = (
    "log_amount",
    "device_trust_score",
    "account_age_years",
    "hour_sin",
    "hour_cos",
    "velocity_1h",
    "distance_100km",
    "chargeback_history",
    "is_new_device",
    *(f"merchant_{value}" for value in MERCHANT_CATEGORIES),
    *(f"country_{value}" for value in COUNTRIES),
    *(f"currency_{value}" for value in CURRENCIES),
)


def vectorize(transaction: Transaction) -> np.ndarray:
    hour = transaction.event_time.hour
    values: list[float] = [
        math.log1p(transaction.amount),
        transaction.device_trust_score,
        min(transaction.account_age_days / 365.0, 20.0),
        math.sin(2 * math.pi * hour / 24),
        math.cos(2 * math.pi * hour / 24),
        min(transaction.velocity_1h / 20.0, 10.0),
        min(transaction.distance_km / 100.0, 100.0),
        min(float(transaction.chargeback_history), 20.0),
        float(transaction.is_new_device),
    ]
    values.extend(float(transaction.merchant_category == item) for item in MERCHANT_CATEGORIES)
    values.extend(float(transaction.country == item) for item in COUNTRIES)
    values.extend(float(transaction.currency == item) for item in CURRENCIES)
    return np.asarray(values, dtype=np.float64)


def build_matrix(
    transactions: list[Transaction], *, require_labels: bool = True
) -> tuple[np.ndarray, np.ndarray | None]:
    if not transactions:
        raise ValueError("At least one transaction is required")
    features = np.vstack([vectorize(transaction) for transaction in transactions])
    if not require_labels:
        return features, None
    labels_list = [transaction.is_fraud for transaction in transactions]
    if any(label is None for label in labels_list):
        raise ValueError("All transactions must have is_fraud labels")
    labels = np.asarray(
        [int(label) for label in labels_list if label is not None],
        dtype=np.float64,
    )
    return features, labels
