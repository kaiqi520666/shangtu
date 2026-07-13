from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.core.providers.turnstile import TurnstileVerificationError, verify_turnstile


def client_context(client):
    context = AsyncMock()
    context.__aenter__.return_value = client
    return context


@pytest.mark.asyncio
async def test_turnstile_accepts_matching_action(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "test-secret")
    response = Mock()
    response.json.return_value = {"success": True, "action": "login"}
    client = AsyncMock()
    client.post.return_value = response

    with patch(
        "app.core.providers.turnstile.httpx.AsyncClient",
        return_value=client_context(client),
    ):
        await verify_turnstile("token", "203.0.113.8", "login")

    client.post.assert_awaited_once()
    assert client.post.await_args.kwargs["data"] == {
        "secret": "test-secret",
        "response": "token",
        "remoteip": "203.0.113.8",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"success": False, "error-codes": ["invalid-input-response"]},
        {"success": True, "action": "register_email"},
    ],
)
async def test_turnstile_rejects_invalid_result_or_action(monkeypatch, payload):
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "test-secret")
    response = Mock()
    response.json.return_value = payload
    client = AsyncMock()
    client.post.return_value = response

    with (
        patch(
            "app.core.providers.turnstile.httpx.AsyncClient",
            return_value=client_context(client),
        ),
        pytest.raises(TurnstileVerificationError, match="重新完成人机验证"),
    ):
        await verify_turnstile("token", "203.0.113.8", "login")


@pytest.mark.asyncio
async def test_turnstile_fails_closed_on_network_error(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET_KEY", "test-secret")
    client = AsyncMock()
    client.post.side_effect = httpx.ConnectError("offline")

    with (
        patch(
            "app.core.providers.turnstile.httpx.AsyncClient",
            return_value=client_context(client),
        ),
        pytest.raises(TurnstileVerificationError, match="服务暂时不可用"),
    ):
        await verify_turnstile("token", "203.0.113.8", "login")
