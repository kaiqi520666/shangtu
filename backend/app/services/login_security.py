from dataclasses import dataclass
from typing import Any

from app.core.rate_limit import hashed_identifier, increment_fixed_window, read_counter


LOGIN_WINDOW_SECONDS = 900
EMAIL_CAPTCHA_THRESHOLD = 3
IP_CAPTCHA_THRESHOLD = 10
IP_FAILURE_LIMIT = 30


@dataclass(frozen=True)
class LoginSecurityState:
    captcha_required: bool
    rate_limited: bool
    retry_after_seconds: int | None = None


def _failure_keys(email: str, ip_address: str) -> tuple[str, str]:
    return (
        f"auth:login:fail:email:{hashed_identifier(email)}",
        f"auth:login:fail:ip:{hashed_identifier(ip_address)}",
    )


async def get_login_security_state(
    redis: Any,
    email: str,
    ip_address: str,
) -> LoginSecurityState:
    email_key, ip_key = _failure_keys(email, ip_address)
    email_failures = await read_counter(redis, email_key)
    ip_failures = await read_counter(redis, ip_key)
    if ip_failures >= IP_FAILURE_LIMIT:
        ttl = await redis.ttl(ip_key)
        return LoginSecurityState(True, True, max(int(ttl), 1))
    return LoginSecurityState(
        email_failures >= EMAIL_CAPTCHA_THRESHOLD or ip_failures >= IP_CAPTCHA_THRESHOLD,
        False,
    )


async def record_login_failure(redis: Any, email: str, ip_address: str) -> LoginSecurityState:
    email_key, ip_key = _failure_keys(email, ip_address)
    await increment_fixed_window(redis, email_key, LOGIN_WINDOW_SECONDS)
    await increment_fixed_window(redis, ip_key, LOGIN_WINDOW_SECONDS)
    return await get_login_security_state(redis, email, ip_address)


async def clear_login_failures(redis: Any, email: str, ip_address: str) -> None:
    await redis.delete(*_failure_keys(email, ip_address))
