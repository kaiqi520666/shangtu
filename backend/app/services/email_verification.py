import hashlib
import hmac
import re
import secrets
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import require_env
from app.core.providers.turnstile import TurnstileVerificationError, verify_turnstile
from app.core.providers.tencent_ses import send_verification_email
from app.core.rate_limit import hashed_identifier, increment_fixed_window
from app.models import User


CODE_TTL_SECONDS = 600
COOLDOWN_SECONDS = 60
EMAIL_HOURLY_LIMIT = 5
IP_HOURLY_LIMIT = 20
MAX_VERIFY_ATTEMPTS = 5
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class EmailVerificationError(ValueError):
    pass


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if len(normalized) > 100 or not EMAIL_PATTERN.fullmatch(normalized):
        raise EmailVerificationError("请输入有效邮箱")
    return normalized


def _code_digest(email: str, code: str) -> str:
    return hmac.new(
        require_env("SECRET_KEY").encode(),
        f"{email}:{code}".encode(),
        hashlib.sha256,
    ).hexdigest()


async def _increment_limit(redis: Any, key: str, limit: int, message: str) -> None:
    count = await increment_fixed_window(redis, key, 3600)
    if count > limit:
        raise EmailVerificationError(message)


async def issue_registration_code(
    db: AsyncSession,
    redis: Any,
    email: str,
    ip_address: str,
    captcha_token: str,
    *,
    send_email: Callable[[str, str], Awaitable[None]] = send_verification_email,
    verify_captcha: Callable[[str, str, str], Awaitable[None]] = verify_turnstile,
) -> str:
    try:
        await verify_captcha(captcha_token, ip_address, "register_email")
    except TurnstileVerificationError as exc:
        raise EmailVerificationError(str(exc)) from exc
    normalized = normalize_email(email)
    existing = await db.execute(select(User.id).where(User.email == normalized))
    if existing.scalar_one_or_none() is not None:
        raise EmailVerificationError("邮箱已注册")

    email_id = hashed_identifier(normalized)
    cooldown_key = f"auth:email-code:cooldown:{email_id}"
    if not await redis.set(cooldown_key, "1", ex=COOLDOWN_SECONDS, nx=True):
        raise EmailVerificationError("请稍后再发送验证码")

    code_key = f"auth:email-code:value:{email_id}"
    attempts_key = f"auth:email-code:attempts:{email_id}"
    try:
        await _increment_limit(
            redis,
            f"auth:email-code:email-limit:{email_id}",
            EMAIL_HOURLY_LIMIT,
            "该邮箱发送过于频繁，请稍后再试",
        )
        await _increment_limit(
            redis,
            f"auth:email-code:ip-limit:{hashed_identifier(ip_address)}",
            IP_HOURLY_LIMIT,
            "请求过于频繁，请稍后再试",
        )
        code = f"{secrets.randbelow(1_000_000):06d}"
        await redis.set(code_key, _code_digest(normalized, code), ex=CODE_TTL_SECONDS)
        await redis.delete(attempts_key)
        await send_email(normalized, code)
    except EmailVerificationError:
        raise
    except Exception as exc:
        await redis.delete(code_key, attempts_key, cooldown_key)
        raise EmailVerificationError("验证码邮件发送失败，请稍后重试") from exc
    return normalized


async def consume_registration_code(redis: Any, email: str, code: str) -> str:
    normalized = normalize_email(email)
    if not re.fullmatch(r"\d{6}", code):
        raise EmailVerificationError("请输入 6 位验证码")

    email_id = hashed_identifier(normalized)
    code_key = f"auth:email-code:value:{email_id}"
    attempts_key = f"auth:email-code:attempts:{email_id}"
    stored_digest = await redis.get(code_key)
    if stored_digest is None:
        raise EmailVerificationError("验证码已过期，请重新获取")
    if isinstance(stored_digest, bytes):
        stored_digest = stored_digest.decode()

    attempts = await redis.incr(attempts_key)
    if attempts == 1:
        await redis.expire(attempts_key, CODE_TTL_SECONDS)
    if not hmac.compare_digest(stored_digest, _code_digest(normalized, code)):
        if attempts >= MAX_VERIFY_ATTEMPTS:
            await redis.delete(code_key, attempts_key)
            raise EmailVerificationError("验证码错误次数过多，请重新获取")
        raise EmailVerificationError("验证码错误")

    await redis.delete(
        code_key,
        attempts_key,
        f"auth:email-code:cooldown:{email_id}",
    )
    return normalized
