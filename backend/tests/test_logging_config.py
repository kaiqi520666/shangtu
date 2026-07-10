import json
import logging

from app.core.logging_config import JsonLogFormatter, task_log_extra


def test_json_log_formatter_emits_task_fields_and_redacts_secrets():
    record = logging.LogRecord(
        name="app.worker.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg=(
            "Authorization=Bearer-secret "
            "https://example.test/result?token=private&signature=signed"
        ),
        args=(),
        exc_info=None,
    )
    for key, value in task_log_extra(
        event="provider_created",
        task_id="task-1",
        job_id="job-1",
        provider_task_id="provider-1",
        scenario="digital_human",
        media_type="video",
        phase="provider_create",
        status="processing",
        retry_count=2,
        duration_ms=12.345,
    ).items():
        setattr(record, key, value)

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["event"] == "provider_created"
    assert payload["retry_count"] == 2
    assert payload["duration_ms"] == 12.35
    assert "private" not in payload["message"]
    assert "signed" not in payload["message"]
    assert "Bearer-secret" not in payload["message"]


def test_task_log_extra_clamps_timing_and_ignores_unknown_fields():
    extra = task_log_extra(
        event="task_started",
        duration_ms=-1,
        queue_duration_ms=-5,
        retry_count=-2,
        payload="must-not-be-logged",
    )

    assert extra == {
        "event": "task_started",
        "retry_count": 0,
        "duration_ms": 0,
        "queue_duration_ms": 0,
    }
