import json
from unittest.mock import Mock

import pytest

from app.core.config import require_env, validate_runtime_config
from app.main import handle_unexpected_exception


def test_required_environment_variable_rejects_empty_value(monkeypatch):
    monkeypatch.delenv("MISSING_REQUIRED_SETTING", raising=False)

    with pytest.raises(RuntimeError, match="MISSING_REQUIRED_SETTING 未配置"):
        require_env("MISSING_REQUIRED_SETTING")


def test_runtime_config_requires_enabled_video_provider_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("VIDEO_PROVIDER", "topenrouter")
    monkeypatch.delenv("TOPENROUTER_KEY", raising=False)
    monkeypatch.delenv("TOPENROUTER_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="TOPENROUTER_KEY 未配置"):
        validate_runtime_config()


def test_runtime_config_rejects_invalid_redis_url(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("REDIS_URL", "http://localhost:6379")

    with pytest.raises(RuntimeError, match="REDIS_URL 格式不正确"):
        validate_runtime_config()


def test_runtime_config_requires_ses_settings(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("VIDEO_PROVIDER", "topenrouter")
    monkeypatch.setenv("TOPENROUTER_KEY", "test-video-key")
    monkeypatch.delenv("TENCENT_CLOUD_SECRET_ID", raising=False)

    with pytest.raises(RuntimeError, match="TENCENT_CLOUD_SECRET_ID 未配置"):
        validate_runtime_config()


@pytest.mark.asyncio
async def test_unexpected_exception_returns_http_500():
    request = Mock()
    request.method = "GET"
    request.url.path = "/broken"

    response = await handle_unexpected_exception(request, RuntimeError("boom"))

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "code": 1,
        "message": "系统异常，请稍后重试",
        "data": None,
    }
