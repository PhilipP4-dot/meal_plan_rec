import json
import logging

from app.logger import JsonFormatter


def test_json_formatter_emits_searchable_context():
    record = logging.LogRecord(
        name="web.app",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-456"
    record.method = "GET"
    record.path = "/health"
    record.status_code = 200
    record.duration_ms = 4.25

    event = json.loads(JsonFormatter().format(record))

    assert event["message"] == "request_completed"
    assert event["request_id"] == "request-456"
    assert event["status_code"] == 200
    assert event["duration_ms"] == 4.25
    assert event["timestamp"].endswith("+00:00")
