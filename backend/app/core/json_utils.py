import json
from typing import Any


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def dump_json_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return dump_json(value)


def parse_json_or_none(raw: str | None):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def parse_json_object(raw: str | None) -> dict:
    parsed = parse_json_or_none(raw)
    return parsed if isinstance(parsed, dict) else {}
