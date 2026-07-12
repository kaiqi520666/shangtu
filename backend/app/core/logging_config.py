from datetime import datetime, timezone
import json
import logging
import re

from app.core.config import get_env

STRUCTURED_FIELDS = (
    "event",
    "task_id",
    "job_id",
    "provider_task_id",
    "scenario",
    "media_type",
    "phase",
    "status",
    "retry_count",
    "duration_ms",
    "queue_duration_ms",
)
SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(authorization|api[_-]?key|access[_-]?token|secret)\b(\s*[:=]\s*)([^\s,;]+)"
)
SECRET_QUERY = re.compile(
    r"(?i)([?&](?:token|sign|signature|key|api_key|access_token|ossaccesskeyid)=)[^&\s]+"
)


def redact_log_text(value: object) -> str:
    text = str(value)
    text = SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}{match.group(2)}***", text)
    return SECRET_QUERY.sub(lambda match: f"{match.group(1)}***", text)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_log_text(record.getMessage()),
        }
        for field in STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None and value != "":
                payload[field] = value
        if record.exc_info:
            payload["exception"] = redact_log_text(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging() -> None:
    level_name = get_env("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def task_log_extra(**values) -> dict:
    extra = {key: values.get(key) for key in STRUCTURED_FIELDS if values.get(key) is not None}
    if "duration_ms" in extra:
        extra["duration_ms"] = max(0, round(float(extra["duration_ms"]), 2))
    if "queue_duration_ms" in extra:
        extra["queue_duration_ms"] = max(0, round(float(extra["queue_duration_ms"]), 2))
    if "retry_count" in extra:
        extra["retry_count"] = max(0, int(extra["retry_count"]))
    return extra
