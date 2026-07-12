from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.digital_human_assets import archive_audio_asset, audio_asset_payload


def test_audio_asset_payload_normalizes_persisted_fields():
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    asset = SimpleNamespace(
        id="audio-1",
        name="商品介绍",
        audio_url="https://example.test/audio.wav",
        object_key="audio/audio-1.wav",
        duration_seconds=12.4,
        size=1024,
        content_type="audio/wav",
        source="upload",
        enabled=True,
        created_at=created_at,
        updated_at=created_at,
    )

    payload = audio_asset_payload(asset)

    assert payload["id"] == "audio-1"
    assert payload["duration_seconds"] == 12
    assert payload["size"] == 1024
    assert payload["enabled"] is True


@pytest.mark.asyncio
async def test_archive_audio_asset_marks_owned_asset():
    asset = SimpleNamespace(enabled=True, archived_at=None)
    db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())

    with patch(
        "app.services.digital_human_assets.get_available_audio_asset",
        AsyncMock(return_value=asset),
    ):
        error_message = await archive_audio_asset(
            db,
            audio_asset_id="audio-1",
            user_id=7,
        )

    assert error_message is None
    assert asset.enabled is False
    assert asset.archived_at is not None
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()