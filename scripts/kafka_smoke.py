"""Publish synthetic events to Kafka and consume them back with validation."""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

from confluent_kafka import Consumer

from sentinelflow.data.generator import generate_transactions
from sentinelflow.domain.schemas import Transaction


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))
    from pipelines.kafka.producer import publish_transactions

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-servers", default="redpanda:9092")
    parser.add_argument("--topic", default="sentinelflow-smoke")
    parser.add_argument("--messages", type=int, default=3)
    args = parser.parse_args()
    if args.messages <= 0:
        parser.error("--messages must be positive")

    events = generate_transactions(args.messages, seed=42)
    publish_transactions(events, args.bootstrap_servers, args.topic)

    consumer = Consumer(
        {
            "bootstrap.servers": args.bootstrap_servers,
            "group.id": f"sentinelflow-smoke-{uuid.uuid4().hex}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumed: list[str] = []
    consumer.subscribe([args.topic])
    deadline = time.monotonic() + 20
    try:
        while len(consumed) < len(events) and time.monotonic() < deadline:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                raise RuntimeError(str(message.error()))
            if message.value() is None:
                continue
            payload = json.loads(message.value().decode())
            transaction = Transaction.from_mapping(payload)
            consumed.append(transaction.transaction_id)
        if len(consumed) != len(events):
            raise RuntimeError(f"Expected {len(events)} events, consumed {len(consumed)}")
        consumer.commit(asynchronous=False)
    finally:
        consumer.close()

    print(json.dumps({"published": len(events), "consumed": len(consumed), "topic": args.topic}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
