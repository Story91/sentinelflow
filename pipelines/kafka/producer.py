"""Kafka producer adapter for transaction events."""

from __future__ import annotations

import json
from collections.abc import Iterable

from sentinelflow.domain.schemas import Transaction


def publish_transactions(events: Iterable[Transaction], bootstrap_servers: str, topic: str) -> None:
    try:
        from confluent_kafka import Producer
    except ImportError as exc:
        raise RuntimeError("Install sentinelflow[data] to use the Kafka adapter") from exc

    producer = Producer({"bootstrap.servers": bootstrap_servers, "enable.idempotence": True})
    failures: list[str] = []

    def on_delivery(error, message) -> None:
        if error is not None:
            failures.append(f"{message.key()!r}: {error}")

    for event in events:
        producer.produce(
            topic,
            json.dumps(event.to_mapping()).encode("utf-8"),
            key=event.transaction_id,
            on_delivery=on_delivery,
        )
        producer.poll(0)
    undelivered = producer.flush(10)
    if undelivered or failures:
        detail = "; ".join(failures[:5])
        raise RuntimeError(f"Kafka delivery failed; undelivered={undelivered}; {detail}")
