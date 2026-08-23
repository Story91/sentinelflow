from datetime import UTC, datetime

import pytest

from sentinelflow.domain.schemas import DomainValidationError, Transaction


def valid_row() -> dict[str, object]:
    return {
        "transaction_id": "txn_1",
        "customer_id": "cust_1",
        "event_time": "2026-01-01T12:00:00Z",
        "amount": "100.50",
        "currency": "PLN",
        "merchant_category": "grocery",
        "country": "PL",
        "device_trust_score": "0.9",
        "account_age_days": "100",
        "is_new_device": "false",
        "velocity_1h": "2",
        "distance_km": "10",
        "chargeback_history": "0",
        "is_fraud": "0",
    }


def test_transaction_parses_and_normalizes() -> None:
    transaction = Transaction.from_mapping(valid_row())
    assert transaction.currency == "PLN"
    assert transaction.is_new_device is False
    assert transaction.event_time == datetime(2026, 1, 1, 12, tzinfo=UTC)


def test_transaction_rejects_unknown_country() -> None:
    row = valid_row()
    row["country"] = "XX"
    with pytest.raises(DomainValidationError, match="unsupported country"):
        Transaction.from_mapping(row)
