from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.heygen_task_lifecycle import (
    provider_task_status,
    refund_video_task_if_needed,
    sync_video_job_status,
    task_progress,
)


@pytest.mark.parametrize(
    ("provider_status", "video_url", "error", "expected"),
    [
        ("pending", None, None, "pending"),
        ("rendering", None, None, "processing"),
        ("completed", None, None, "done"),
        ("unknown", "https://example.com/video.mp4", None, "done"),
        ("unknown", None, "provider failed", "failed"),
    ],
)
def test_provider_task_status(provider_status, video_url, error, expected):
    assert provider_task_status(
        provider_status,
        video_url=video_url,
        failure_message=error,
    ) == expected


def test_task_progress():
    assert [task_progress(status) for status in ["pending", "processing", "done", "failed"]] == [10, 65, 100, 0]


@pytest.mark.asyncio
async def test_refund_video_task_is_idempotent():
    db = AsyncMock()
    task = SimpleNamespace(user_id=3, credit_cost=12, credit_refunded=False)

    with patch(
        "app.services.heygen_task_lifecycle.refund_user_credits",
        AsyncMock(return_value=88),
    ) as refund:
        assert await refund_video_task_if_needed(db, task, note="refund") == 88
        assert await refund_video_task_if_needed(db, task, note="refund") is None

    refund.assert_awaited_once_with(db, 3, 12, note="refund")


@pytest.mark.asyncio
async def test_sync_video_job_status_keeps_mixed_tasks_generating():
    job = SimpleNamespace(status="draft", updated_at=None)
    result = SimpleNamespace(
        all=lambda: [
            ("done", "https://example.com/video.mp4", None, datetime.now(timezone.utc)),
            ("failed", None, "failed", datetime.now(timezone.utc)),
        ]
    )
    db = AsyncMock()
    db.get = AsyncMock(return_value=job)
    db.execute = AsyncMock(return_value=result)

    await sync_video_job_status(db, job_id="job-1", scenario="digital_human")

    assert job.status == "generating"
