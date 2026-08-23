"""Deterministic synthetic transaction generator.

The dataset is intentionally synthetic so the repository can be published and
run without exposing personal or payment data. The label is generated from an
explicit risk function, which makes drift and failure-mode exercises repeatable.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

from sentinelflow.domain.schemas import Transaction

CSV_FIELDS = list(Transaction.__dataclass_fields__)


def _sigmoid(value: np.ndarray) -> np.ndarray:
    clipped = np.clip(value, -30, 30)
    return np.asarray(1 / (1 + np.exp(-clipped)), dtype=np.float64)


def generate_transactions(rows: int, seed: int = 42) -> list[Transaction]:
    if rows < 2:
        raise ValueError("rows must be at least 2")
    rng = np.random.default_rng(seed)
    merchant_categories = np.array(
        ["grocery", "electronics", "travel", "gaming", "fashion", "utilities"]
    )
    countries = np.array(["PL", "DE", "FR", "GB", "US", "ES", "IT"])
    currencies = np.array(["PLN", "EUR", "GBP", "USD"])
    start = datetime(2026, 1, 1, tzinfo=UTC)
    events: list[Transaction] = []

    for index in range(rows):
        amount = float(np.round(np.exp(rng.normal(4.1, 1.05)), 2))
        device_trust = float(np.round(rng.beta(7, 2), 4))
        account_age = int(rng.integers(3, 2_500))
        is_new_device = bool(rng.random() < 0.14)
        velocity = int(rng.poisson(2.3))
        distance = float(np.round(np.abs(rng.normal(45, 75)), 2))
        chargebacks = int(rng.poisson(0.12))
        merchant = str(rng.choice(merchant_categories))
        country = str(rng.choice(countries))
        currency = str(rng.choice(currencies))
        hour = int(rng.integers(0, 24))

        logit = (
            -4.2
            + 0.45 * np.log1p(amount)
            + 1.8 * (1 - device_trust)
            + 0.9 * is_new_device
            + 0.22 * velocity
            + 0.006 * distance
            + 0.75 * chargebacks
            + 0.55 * (merchant in {"gaming", "electronics"})
            + 0.7 * (hour in {0, 1, 2, 3, 4})
            + 0.5 * (account_age < 30)
        )
        label = int(rng.random() < float(_sigmoid(np.array([logit]))[0]))
        event_time = start + timedelta(minutes=index * 7 + int(rng.integers(0, 6)))
        events.append(
            Transaction(
                transaction_id=f"txn_{index:08d}",
                customer_id=f"cust_{int(rng.integers(1, max(2, rows // 3))):06d}",
                event_time=event_time,
                amount=amount,
                currency=currency,
                merchant_category=merchant,
                country=country,
                device_trust_score=device_trust,
                account_age_days=account_age,
                is_new_device=is_new_device,
                velocity_1h=velocity,
                distance_km=distance,
                chargeback_history=chargebacks,
                is_fraud=label,
            )
        )
    return events


def write_transactions(events: Iterable[Transaction], output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for event in events:
            writer.writerow(event.to_mapping())
            count += 1
    return count
