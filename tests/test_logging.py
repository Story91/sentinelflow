import json
import logging

from sentinelflow.observability.logging import JsonFormatter


def test_json_formatter_emits_only_allowlisted_context() -> None:
    record = logging.LogRecord(
        name="sentinelflow",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="risk prediction completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "req_test"
    record.model_version = "version_test"
    record.customer_id = "must-not-be-logged"
    record.raw_payload = {"card_number": "must-not-be-logged"}

    payload = json.loads(JsonFormatter().format(record))

    assert payload["request_id"] == "req_test"
    assert payload["model_version"] == "version_test"
    assert "customer_id" not in payload
    assert "raw_payload" not in payload
    assert "must-not-be-logged" not in json.dumps(payload)
