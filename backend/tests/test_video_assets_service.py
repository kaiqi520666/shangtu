import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.oss import UploadedFile
from app.models import UserAudioAsset, VideoTask
from app.services.video_assets import create_reference_audio, create_uploaded_video


def uploaded_file():
    return UploadedFile(
        url="https://example.test/upload.mp4",
        object_key="video-uploads/7/upload.mp4",
        content_type="video/mp4",
        size=1024,
    )


def database(*, commit_error: Exception | None = None):
    db = SimpleNamespace(
        add=Mock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    async def commit():
        if commit_error:
            raise commit_error
        item = db.add.call_args.args[0]
        if isinstance(item, UserAudioAsset) and item.id is None:
            item.id = "audio-1"

    db.commit.side_effect = commit
    return db


@pytest.mark.asyncio
async def test_create_uploaded_video_persists_completed_task():
    db = database()
    uploaded = uploaded_file()
    with patch("app.services.video_assets.upload_video_bytes", AsyncMock(return_value=uploaded)) as upload:
        outcome = await create_uploaded_video(
            db,
            user_id=7,
            content=b"video",
            content_type="video/mp4",
            filename=" 商品演示.mp4 ",
        )

    assert outcome.error_message is None
    assert outcome.uploaded is uploaded
    upload.assert_awaited_once_with(
        user_id=7,
        content=b"video",
        content_type="video/mp4",
        source="video-uploads",
    )
    task = db.add.call_args.args[0]
    assert isinstance(task, VideoTask)
    assert (task.title, task.status, task.result_url, task.credit_cost) == (
        "商品演示.mp4",
        "done",
        uploaded.url,
        0,
    )
    assert json.loads(task.settings_snapshot_json) == {
        "source": "upload",
        "object_key": uploaded.object_key,
        "content_type": uploaded.content_type,
        "size": uploaded.size,
    }
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_reference_audio_persists_asset():
    db = database()
    uploaded = UploadedFile(
        url="https://example.test/upload.mp3",
        object_key="video-audio-uploads/7/upload.mp3",
        content_type="audio/mpeg",
        size=512,
    )
    with patch("app.services.video_assets.upload_audio_bytes", AsyncMock(return_value=uploaded)) as upload:
        outcome = await create_reference_audio(
            db,
            user_id=7,
            content=b"audio",
            content_type="audio/mpeg",
            filename=" 参考口播.mp3 ",
        )

    assert outcome.error_message is None
    assert outcome.uploaded is uploaded
    assert outcome.asset_id == "audio-1"
    upload.assert_awaited_once_with(
        user_id=7,
        content=b"audio",
        content_type="audio/mpeg",
        source="video-audio-uploads",
    )
    asset = db.add.call_args.args[0]
    assert isinstance(asset, UserAudioAsset)
    assert (asset.user_id, asset.name, asset.audio_url, asset.source) == (
        7,
        "参考口播.mp3",
        uploaded.url,
        "upload",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("creator", "upload_name", "message"),
    [
        (create_uploaded_video, "upload_video_bytes", "视频格式不支持"),
        (create_reference_audio, "upload_audio_bytes", "音频格式不支持"),
    ],
)
async def test_asset_creation_returns_upload_validation_error(creator, upload_name, message):
    db = database()
    with patch(f"app.services.video_assets.{upload_name}", AsyncMock(side_effect=ValueError(message))):
        outcome = await creator(
            db,
            user_id=7,
            content=b"invalid",
            content_type="application/octet-stream",
            filename="invalid.bin",
        )

    assert outcome.error_message == message
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("creator", "upload_name", "error_message"),
    [
        (create_uploaded_video, "upload_video_bytes", "视频上传失败"),
        (create_reference_audio, "upload_audio_bytes", "音频上传失败"),
    ],
)
async def test_asset_creation_rolls_back_persistence_failure(creator, upload_name, error_message):
    db = database(commit_error=RuntimeError("database offline"))
    uploaded = uploaded_file()
    with patch(f"app.services.video_assets.{upload_name}", AsyncMock(return_value=uploaded)):
        outcome = await creator(
            db,
            user_id=7,
            content=b"content",
            content_type=uploaded.content_type,
            filename="upload.mp4",
        )

    assert outcome.error_message == error_message
    db.rollback.assert_awaited_once()
