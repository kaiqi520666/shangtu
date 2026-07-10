from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.media_projection import audio_asset_select, image_asset_select, includes_audio, video_asset_select
from app.routers.asset import download_asset, list_assets


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value

    def scalar_one_or_none(self):
        return self.value


class MappingResult:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return self

    def all(self):
        return self.rows


def test_asset_projections_share_normalized_columns():
    expected = [
        "task_id",
        "media_type",
        "result_url",
        "title",
        "type_id",
        "scenario",
        "job_title",
        "created_at",
        "source",
        "duration_seconds",
        "size",
        "content_type",
    ]
    assert list(image_asset_select(1, None).selected_columns.keys()) == expected
    assert list(video_asset_select(1, None).selected_columns.keys()) == expected
    assert list(audio_asset_select(1, None).selected_columns.keys()) == expected


def test_unfiltered_assets_include_audio():
    assert includes_audio(None) is True
    assert includes_audio("") is True
    assert includes_audio("audio") is True
    assert includes_audio("image") is False


@pytest.mark.asyncio
async def test_list_assets_returns_audio_metadata():
    created_at = datetime(2026, 7, 10, tzinfo=UTC)
    row = {
        "task_id": "audio-1",
        "media_type": "audio",
        "result_url": "https://example.com/audio.wav",
        "title": "口播",
        "type_id": "audio",
        "scenario": "",
        "job_title": "",
        "created_at": created_at,
        "source": "upload",
        "duration_seconds": 12,
        "size": 2048,
        "content_type": "audio/wav",
    }
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[ScalarResult(1), MappingResult([row])])

    response = await list_assets(
        scenario=None,
        media_type="audio",
        page=1,
        page_size=20,
        current_user=SimpleNamespace(id=7),
        db=db,
    )

    assert response.code == 0
    assert response.data["items"][0] == {
        **row,
        "created_at": "2026-07-10T00:00:00Z",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("media_type", "asset", "fallback_extension"),
    [
        ("image", SimpleNamespace(result_url="https://example.com/image.png"), "png"),
        ("video", SimpleNamespace(result_url="https://example.com/video.mp4"), "mp4"),
        (
            "audio",
            SimpleNamespace(audio_url="https://example.com/audio", content_type="audio/wav"),
            "wav",
        ),
    ],
)
async def test_download_asset_uses_owned_asset(media_type, asset, fallback_extension):
    db = AsyncMock()
    db.execute = AsyncMock(return_value=ScalarResult(asset))
    sentinel = object()

    with patch("app.routers.asset.remote_media_download_response", return_value=sentinel) as download:
        response = await download_asset(
            media_type=media_type,
            asset_id="asset-1",
            current_user=SimpleNamespace(id=7),
            db=db,
        )

    assert response is sentinel
    download.assert_called_once_with(
        asset.result_url if media_type != "audio" else asset.audio_url,
        filename_stem="asset-1",
        fallback_extension=fallback_extension,
        media_type_override=asset.content_type if media_type == "audio" else None,
    )


@pytest.mark.asyncio
async def test_download_asset_rejects_missing_or_unknown_asset():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=ScalarResult(None))

    missing = await download_asset("audio", "missing", SimpleNamespace(id=7), db)
    unknown = await download_asset("document", "asset-1", SimpleNamespace(id=7), db)

    assert missing.code == 1
    assert missing.message == "资产不存在或不可下载"
    assert unknown.code == 1
    assert unknown.message == "不支持的资产类型"
