"""Privacy-by-design helpers for the synthetic transaction domain."""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta


def pseudonymize_identifier(identifier: str, secret: str) -> str:
    """Return a stable, non-reversible identifier for joins and audit logs."""
    if not secret or secret == "change-me-locally":
        raise ValueError("A non-default HMAC secret is required")
    digest = hmac.new(secret.encode(), identifier.encode(), hashlib.sha256).hexdigest()
    return f"psn_{digest[:24]}"


def retention_cutoff(*, retention_days: int, now: datetime | None = None) -> datetime:
    if retention_days <= 0:
        raise ValueError("retention_days must be positive")
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(UTC) - timedelta(days=retention_days)


def is_expired(event_time: datetime, *, retention_days: int, now: datetime | None = None) -> bool:
    return event_time.astimezone(UTC) < retention_cutoff(retention_days=retention_days, now=now)
