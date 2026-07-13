from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.auth import hash_password
from app.core.time import utc_now
from app.routers import auth
from app.services.login_security import get_login_security_state, record_login_failure
from tests.fake_redis import FakeRedis


def login_request(redis, ip_address="203.0.113.8"):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(redis_pool=redis)),
        headers={"x-real-ip": ip_address},
        client=SimpleNamespace(host="172.18.0.2"),
    )


def login_db(user=None):
    result = Mock()
    result.scalar_one_or_none.return_value = user
    return SimpleNamespace(execute=AsyncMock(return_value=result))


def active_user():
    return SimpleNamespace(
        id=1,
        username="user",
        email="user@example.com",
        password_hash=hash_password("correct-password"),
        auth_version=0,
        credits=0,
        consumption_multiplier=Decimal("1.00"),
        distribution_level=None,
        distribution_enabled=False,
        role="user",
        status="active",
        created_at=utc_now(),
    )


@pytest.mark.asyncio
async def test_login_requires_captcha_after_third_email_failure(monkeypatch):
    redis = FakeRedis()
    db = login_db()
    request = login_request(redis)

    for attempt in range(3):
        response = await auth.login(
            auth.LoginRequest(email="user@example.com", password="wrong"),
            request,
            db,
        )
        assert response.data["captcha_required"] is (attempt == 2)

    db_calls = db.execute.await_count
    response = await auth.login(
        auth.LoginRequest(email="user@example.com", password="wrong"),
        request,
        db,
    )
    assert response.message == "请完成人机验证"
    assert response.data == {"captcha_required": True}
    assert db.execute.await_count == db_calls


@pytest.mark.asyncio
async def test_captcha_login_success_clears_failure_counters(monkeypatch):
    redis = FakeRedis()
    for _ in range(3):
        await record_login_failure(redis, "user@example.com", "203.0.113.8")
    verify = AsyncMock()
    monkeypatch.setattr(auth, "verify_turnstile", verify)

    response = await auth.login(
        auth.LoginRequest(
            email="user@example.com",
            password="correct-password",
            captcha_token="captcha-token",
        ),
        login_request(redis),
        login_db(active_user()),
    )

    assert response.code == 0
    assert response.data["token"]
    verify.assert_awaited_once_with("captcha-token", "203.0.113.8", "login")
    assert not redis.values


@pytest.mark.asyncio
async def test_login_ip_limit_returns_retry_without_database_query():
    redis = FakeRedis()
    for index in range(30):
        await record_login_failure(redis, f"user{index}@example.com", "203.0.113.8")
    db = login_db()

    response = await auth.login(
        auth.LoginRequest(email="blocked@example.com", password="wrong"),
        login_request(redis),
        db,
    )

    assert response.message == "登录尝试过于频繁，请稍后再试"
    assert response.data == {"captcha_required": True, "retry_after_seconds": 900}
    db.execute.assert_not_awaited()
    state = await get_login_security_state(redis, "blocked@example.com", "203.0.113.8")
    assert state.rate_limited is True
