"""Kafka consumer adapter with explicit retry/DLQ boundary."""

from __future__ import annotations

from collections.abc import Callable


def consume_forever(
    bootstrap_servers: str,
    topic: str,
    group_id: str,
    handler: Callable[[bytes], None],
    dead_letter: Callable[[bytes, Exception], None],
) -> None:
    try:
        from confluent_kafka import Consumer
    except ImportError as exc:
        raise RuntimeError("Install sentinelflow[data] to use the Kafka adapter") from exc

    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([topic])
    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                raise RuntimeError(str(message.error()))
            payload = message.value()
            if payload is None:
                # Kafka tombstones are valid records but not transaction events.
                consumer.commit(message=message, asynchronous=False)
                continue
            try:
                handler(payload)
            except Exception as exc:  # noqa: BLE001 - DLQ is the deliberate boundary.
                dead_letter(payload, exc)
            consumer.commit(message=message, asynchronous=False)
    finally:
        consumer.close()
