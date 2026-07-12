from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.video_tasks import archive_video_task, get_video_task_details


@pytest.mark.asyncio
async def test_get_video_task_details_projects_runtime_and_snapshots():
    task = SimpleNamespace(
        id="video-1",
        scenario="product_video",
        status="processing",
        result_url=None,
        error_message=None,
        progress=40,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        prompt="最终提示词",
        prompt_snapshot_json='{"user":"展示商品","final":"最终提示词"}',
        settings_snapshot_json='{"duration":8}',
        input_mode="reference_to_video",
        input_images_json='["https://example.test/product.png"]',
        input_video_url=None,
        duration=8,
        resolution="720p",
        aspect_ratio="9:16",
        credit_cost=36,
    )
    state = SimpleNamespace(
        status="processing",
        result_url=None,
        error_message=None,
        progress=55,
    )
    runtime = SimpleNamespace(
        status="processing",
        result_url=None,
        error_message=None,
        progress=55,
    )
    db = SimpleNamespace()

    with (
        patch(
            "app.services.video_tasks.get_user_video_task",
            AsyncMock(return_value=task),
        ),
        patch("app.services.video_tasks.merge_task_state", AsyncMock(return_value=state)),
        patch("app.services.video_tasks.project_task_runtime_state", return_value=runtime),
        patch("app.services.video_tasks.get_user_credits", AsyncMock(return_value=64)),
    ):
        details = await get_video_task_details(
            db,
            user_id=7,
            task_id="video-1",
            redis_pool=object(),
        )

    assert details["task_id"] == "video-1"
    assert details["progress"] == 55
    assert details["credits"] == 64
    assert details["prompt_snapshot"]["user"] == "展示商品"
    assert details["settings_snapshot"] == {"duration": 8}
    assert details["input_images"] == ["https://example.test/product.png"]


@pytest.mark.asyncio
async def test_archive_video_task_marks_owned_task():
    task = SimpleNamespace(archived=False, archived_at=None)
    db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    archived_at = datetime(2026, 1, 2, tzinfo=UTC)

    with (
        patch(
            "app.services.video_tasks.get_user_video_task",
            AsyncMock(return_value=task),
        ),
        patch("app.services.video_tasks.utc_now", return_value=archived_at),
    ):
        error_message = await archive_video_task(
            db,
            user_id=7,
            task_id="video-1",
        )

    assert error_message is None
    assert task.archived is True
    assert task.archived_at == archived_at
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_archive_video_task_rolls_back_commit_failure():
    task = SimpleNamespace(archived=False, archived_at=None)
    db = SimpleNamespace(
        commit=AsyncMock(side_effect=RuntimeError("offline")),
        rollback=AsyncMock(),
    )

    with patch(
        "app.services.video_tasks.get_user_video_task",
        AsyncMock(return_value=task),
    ):
        error_message = await archive_video_task(
            db,
            user_id=7,
            task_id="video-1",
        )

    assert error_message == "删除失败，请稍后重试"
    db.rollback.assert_awaited_once()