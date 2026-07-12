from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest
from starlette.datastructures import Headers, UploadFile

from app.routers.digital_human import upload_photo_avatar


def make_file() -> UploadFile:
    return UploadFile(
        BytesIO(b"image"),
        filename="avatar.png",
        headers=Headers({"content-type": "image/png"}),
    )


def make_db():
    async def refresh(task):
        now = datetime.now(timezone.utc)
        task.id = task.id or "task-1"
        task.created_at = task.created_at or now
        task.updated_at = task.updated_at or now

    return SimpleNamespace(
        add=Mock(),
        commit=AsyncMock(),
        refresh=AsyncMock(side_effect=refresh),
        rollback=AsyncMock(),
        flush=AsyncMock(),
    )


def client_context():
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=object())
    context.__aexit__ = AsyncMock(return_value=None)
    return context


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_effect", "expected_message"),
    [
        ({"avatar_id": "avatar-1", "status": "pending"}, "success"),
        ({"status": "pending"}, "HeyGen 未返回照片数字人 ID"),
        (httpx.ConnectError("offline"), "HeyGen 暂时不可用"),
        (RuntimeError("boom"), "HeyGen 创建失败，请稍后重试"),
    ],
)
async def test_upload_photo_avatar_returns_current_credits_for_all_provider_paths(
    provider_effect,
    expected_message,
):
    db = make_db()
    create_mock = AsyncMock(
        side_effect=provider_effect if isinstance(provider_effect, Exception) else None,
        return_value=None if isinstance(provider_effect, Exception) else provider_effect,
    )
    uploaded = SimpleNamespace(
        url="https://example.test/avatar.png",
        object_key="avatars/avatar.png",
    )

    with (
        patch("app.routers.digital_human.upload_image_bytes", AsyncMock(return_value=uploaded)),
        patch("app.routers.digital_human.httpx.AsyncClient", return_value=client_context()),
        patch("app.routers.digital_human.create_photo_avatar", create_mock),
        patch("app.routers.digital_human.parse_heygen_error_message", return_value="HeyGen 暂时不可用"),
        patch("app.routers.digital_human._get_user_avatars_by_ids", AsyncMock(return_value={})),
        patch("app.routers.digital_human.get_user_credits", AsyncMock(return_value=73)) as credits,
    ):
        response = await upload_photo_avatar(
            file=make_file(),
            name="测试数字人",
            current_user=SimpleNamespace(id=7),
            db=db,
        )

    assert response.message == expected_message
    assert response.data["credits"] == 73
    assert response.data["credit_cost"] == 0
    credits.assert_awaited()
