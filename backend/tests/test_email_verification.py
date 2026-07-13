import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.providers import tencent_ses
from app.core.providers.turnstile import TurnstileVerificationError
from app.core.time import utc_now
from app.routers import auth
from app.services.email_verification import (
    EmailVerificationError,
    consume_registration_code,
    issue_registration_code,
)
from tests.fake_redis import FakeRedis


def db_with_email(existing=None):
    result = Mock()
    result.scalar_one_or_none.return_value = existing
    return SimpleNamespace(execute=AsyncMock(return_value=result))


async def issue_code(db, redis, email, ip_address, *, send_email):
    return await issue_registration_code(
        db,
        redis,
        email,
        ip_address,
        "captcha-token",
        send_email=send_email,
        verify_captcha=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_issue_code_rejects_invalid_captcha_before_database():
    db = db_with_email()
    sender = AsyncMock()

    with pytest.raises(EmailVerificationError, match="人机验证"):
        await issue_registration_code(
            db,
            FakeRedis(),
            "user@example.com",
            "127.0.0.1",
            "invalid-token",
            send_email=sender,
            verify_captcha=AsyncMock(
                side_effect=TurnstileVerificationError("请重新完成人机验证")
            ),
        )

    db.execute.assert_not_awaited()
    sender.assert_not_awaited()


@pytest.mark.asyncio
async def test_issue_code_normalizes_email_and_stores_only_digest(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    redis = FakeRedis()
    sender = AsyncMock()

    normalized = await issue_code(
        db_with_email(),
        redis,
        " User@Example.com ",
        "127.0.0.1",
        send_email=sender,
    )

    assert normalized == "user@example.com"
    sent_email, sent_code = sender.await_args.args
    assert sent_email == normalized
    assert len(sent_code) == 6 and sent_code.isdigit()
    assert sent_code not in redis.values.values()
    assert any(key.startswith("auth:email-code:value:") for key in redis.values)


@pytest.mark.asyncio
async def test_issue_code_rejects_registered_email_and_cooldown(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    with pytest.raises(EmailVerificationError, match="邮箱已注册"):
        await issue_code(
            db_with_email(existing=1),
            FakeRedis(),
            "user@example.com",
            "127.0.0.1",
            send_email=AsyncMock(),
        )

    redis = FakeRedis()
    sender = AsyncMock()
    await issue_code(
        db_with_email(), redis, "user@example.com", "127.0.0.1", send_email=sender
    )
    with pytest.raises(EmailVerificationError, match="稍后再发送"):
        await issue_code(
            db_with_email(), redis, "user@example.com", "127.0.0.1", send_email=sender
        )
    assert sender.await_count == 1


@pytest.mark.asyncio
async def test_issue_code_cleans_up_after_provider_failure(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    redis = FakeRedis()

    with pytest.raises(EmailVerificationError, match="邮件发送失败"):
        await issue_code(
            db_with_email(),
            redis,
            "user@example.com",
            "127.0.0.1",
            send_email=AsyncMock(side_effect=RuntimeError("offline")),
        )

    assert not any("value" in key or "cooldown" in key for key in redis.values)


@pytest.mark.asyncio
async def test_issue_code_enforces_email_and_ip_hourly_limits(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    redis = FakeRedis()
    sender = AsyncMock()
    for _ in range(5):
        await issue_code(
            db_with_email(), redis, "user@example.com", "127.0.0.1", send_email=sender
        )
        cooldown_key = next(key for key in redis.values if "cooldown" in key)
        await redis.delete(cooldown_key)
    with pytest.raises(EmailVerificationError, match="邮箱发送过于频繁"):
        await issue_code(
            db_with_email(), redis, "user@example.com", "127.0.0.1", send_email=sender
        )
    assert sender.await_count == 5

    redis = FakeRedis()
    sender.reset_mock()
    for index in range(20):
        await issue_code(
            db_with_email(),
            redis,
            f"user{index}@example.com",
            "127.0.0.1",
            send_email=sender,
        )
    with pytest.raises(EmailVerificationError, match="请求过于频繁"):
        await issue_code(
            db_with_email(), redis, "blocked@example.com", "127.0.0.1", send_email=sender
        )
    assert sender.await_count == 20


@pytest.mark.asyncio
async def test_consume_code_limits_failures_and_deletes_success(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    redis = FakeRedis()
    sender = AsyncMock()
    await issue_code(
        db_with_email(), redis, "user@example.com", "127.0.0.1", send_email=sender
    )
    sent_code = sender.await_args.args[1]

    for _ in range(4):
        with pytest.raises(EmailVerificationError, match="验证码错误$"):
            await consume_registration_code(redis, "user@example.com", "000000")
    assert await consume_registration_code(redis, "user@example.com", sent_code) == "user@example.com"
    assert not any("value" in key or "attempts" in key for key in redis.values)

    await issue_code(
        db_with_email(), redis, "other@example.com", "127.0.0.2", send_email=sender
    )
    for attempt in range(5):
        message = "错误次数过多" if attempt == 4 else "验证码错误$"
        with pytest.raises(EmailVerificationError, match=message):
            await consume_registration_code(redis, "other@example.com", "000000")


@pytest.mark.asyncio
async def test_register_requires_code_before_user_creation(monkeypatch):
    consume = AsyncMock(side_effect=EmailVerificationError("验证码错误"))
    monkeypatch.setattr(auth, "consume_registration_code", consume)
    db = db_with_email()
    db.add = Mock()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis_pool=object())))

    response = await auth.register(
        auth.RegisterRequest(
            username="user",
            email=" User@Example.com ",
            password="123456",
            verification_code="000000",
        ),
        request,
        db,
    )

    assert response.code != 0
    consume.assert_awaited_once_with(request.app.state.redis_pool, "user@example.com", "000000")
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_register_consumes_code_and_creates_normalized_user(monkeypatch):
    consume = AsyncMock(return_value="user@example.com")
    monkeypatch.setattr(auth, "consume_registration_code", consume)
    db = db_with_email()
    db.add = Mock()
    db.commit = AsyncMock()

    async def refresh_user(user):
        user.id = 1
        user.auth_version = 0
        user.credits = 0
        user.consumption_multiplier = Decimal("1.00")
        user.distribution_level = None
        user.distribution_enabled = False
        user.role = "user"
        user.status = "active"
        user.created_at = utc_now()

    db.refresh = AsyncMock(side_effect=refresh_user)
    redis = object()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(redis_pool=redis)))

    response = await auth.register(
        auth.RegisterRequest(
            username="user",
            email=" User@Example.com ",
            password="123456",
            verification_code="123456",
        ),
        request,
        db,
    )

    assert response.code == 0
    assert response.data["email"] == "user@example.com"
    assert response.data["token"]
    assert db.add.call_args.args[0].email == "user@example.com"
    consume.assert_awaited_once_with(redis, "user@example.com", "123456")
    db.commit.assert_awaited_once()


def test_tencent_ses_provider_builds_approved_template_request(monkeypatch):
    monkeypatch.setenv("TENCENT_CLOUD_SECRET_ID", "secret-id")
    monkeypatch.setenv("TENCENT_CLOUD_SECRET_KEY", "secret-key")
    monkeypatch.setenv("TENCENT_SES_REGION", "ap-hongkong")
    monkeypatch.setenv("TENCENT_SES_FROM_EMAIL", "no-reply@mail.nodepass.net")
    monkeypatch.setenv("TENCENT_SES_TEMPLATE_ID", "204003")
    client = Mock()
    monkeypatch.setattr(tencent_ses.ses_client, "SesClient", Mock(return_value=client))

    tencent_ses._send_verification_email("user@example.com", "123456")

    request = client.SendEmail.call_args.args[0]
    assert request.FromEmailAddress == "no-reply@mail.nodepass.net"
    assert request.Destination == ["user@example.com"]
    assert request.Template.TemplateID == 204003
    assert json.loads(request.Template.TemplateData) == {"code": "123456"}


@pytest.mark.asyncio
async def test_send_code_route_uses_nginx_real_ip(monkeypatch):
    issue = AsyncMock()
    monkeypatch.setattr(auth, "issue_registration_code", issue)
    redis = object()
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(redis_pool=redis)),
        headers={"x-real-ip": "203.0.113.8"},
        client=SimpleNamespace(host="172.18.0.2"),
    )
    db = db_with_email()

    response = await auth.send_email_code(
        auth.EmailCodeRequest(email="user@example.com", captcha_token="captcha-token"),
        request,
        db,
    )

    assert response.code == 0
    issue.assert_awaited_once_with(
        db,
        redis,
        "user@example.com",
        "203.0.113.8",
        "captcha-token",
    )
