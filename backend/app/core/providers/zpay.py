import hashlib
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.core.config import get_env


def format_amount(amount_cents: int) -> str:
    amount = (Decimal(amount_cents) / Decimal(100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return f"{amount:.2f}"


def parse_amount_cents(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(
            (Decimal(str(value)) * Decimal(100)).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
    except Exception:
        return None


def get_zpay_key() -> str:
    key = get_env("ZPAY_KEY")
    if not key:
        raise ValueError("ZPAY_KEY 未配置")
    return key


def get_zpay_pid() -> str:
    pid = get_env("ZPAY_PID")
    if not pid:
        raise ValueError("ZPAY_PID 未配置")
    return pid


def get_zpay_gateway() -> str:
    return get_env("ZPAY_GATEWAY", "https://zpayz.cn").rstrip("/")


def get_zpay_notify_url() -> str:
    url = get_env("ZPAY_NOTIFY_URL")
    if not url:
        raise ValueError("ZPAY_NOTIFY_URL 未配置")
    return url


def get_zpay_return_url() -> str:
    url = get_env("ZPAY_RETURN_URL")
    if not url:
        raise ValueError("ZPAY_RETURN_URL 未配置")
    return url


def sign_params(params: dict[str, Any], key: str) -> str:
    items = [
        (name, str(value))
        for name, value in params.items()
        if name not in {"sign", "sign_type"} and value is not None and str(value) != ""
    ]
    items.sort(key=lambda item: item[0])
    raw = "&".join(f"{name}={value}" for name, value in items)
    return hashlib.md5(f"{raw}{key}".encode()).hexdigest()
