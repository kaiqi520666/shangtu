from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.worker.heygen_tasks import _run_heygen_task


def make_task(**overrides):
    values = {
        "id": "task-1",
        "job_id": "job-1",
        "scenario": "digital_human",
        "status": "pending",
        "archived": False,
        "provider_task_id": "provider-1",
        "created_at": datetime.now(timezone.utc),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_existing_provider_task_resumes_without_creating_again():
    task = make_task()
    with (
        patch("app.worker.heygen_tasks._load_task", AsyncMock(return_value=task)),
        patch("app.worker.heygen_tasks._create_digital_human", AsyncMock()) as create,
        patch(
            "app.worker.heygen_tasks._poll_digital_human",
            AsyncMock(return_value=("done", "https://example.com/video.mp4", None, 5)),
        ),
        patch("app.worker.heygen_tasks._persist_terminal", AsyncMock()) as persist,
        patch("app.worker.heygen_tasks.set_task_status", AsyncMock()),
        patch("app.worker.heygen_tasks.set_task_progress", AsyncMock()),
    ):
        await _run_heygen_task({"redis": object()}, task.id, task.scenario)

    create.assert_not_awaited()
    persist.assert_awaited_once_with(
        task.id,
        status="done",
        result_url="https://example.com/video.mp4",
        error_message=None,
        duration=5,
    )


@pytest.mark.asyncio
async def test_provider_failure_uses_terminal_refund_path():
    task = make_task()
    ctx = {"redis": object()}
    with (
        patch("app.worker.heygen_tasks._load_task", AsyncMock(return_value=task)),
        patch(
            "app.worker.heygen_tasks._poll_digital_human",
            AsyncMock(return_value=("failed", None, "provider failed", None)),
        ),
        patch("app.worker.heygen_tasks._mark_failed", AsyncMock()) as mark_failed,
        patch("app.worker.heygen_tasks.set_task_status", AsyncMock()),
        patch("app.worker.heygen_tasks.set_task_progress", AsyncMock()),
    ):
        await _run_heygen_task(ctx, task.id, task.scenario)

    mark_failed.assert_awaited_once_with(ctx, task, "provider failed")


@pytest.mark.asyncio
async def test_transient_create_retries_emit_structured_lifecycle_logs(caplog):
    task = make_task(provider_task_id=None)
    create = AsyncMock(
        side_effect=[
            httpx.ConnectError("temporary-1"),
            httpx.ConnectError("temporary-2"),
            "provider-1",
        ]
    )
    caplog.set_level("INFO", logger="app.worker.heygen_tasks")
    with (
        patch("app.worker.heygen_tasks._load_task", AsyncMock(return_value=task)),
        patch("app.worker.heygen_tasks._create_digital_human", create),
        patch(
            "app.worker.heygen_tasks._poll_digital_human",
            AsyncMock(return_value=("done", "https://example.com/video.mp4", None, 5)),
        ),
        patch("app.worker.heygen_tasks._persist_terminal", AsyncMock()),
        patch("app.worker.heygen_tasks.set_task_status", AsyncMock()),
        patch("app.worker.heygen_tasks.set_task_progress", AsyncMock()),
        patch("app.worker.heygen_tasks.asyncio.sleep", AsyncMock()),
    ):
        await _run_heygen_task({"redis": object()}, task.id, task.scenario)

    lifecycle = [record for record in caplog.records if hasattr(record, "event")]
    events = [record.event for record in lifecycle]
    retries = [record.retry_count for record in lifecycle if record.event == "provider_create_retry"]
    assert events == [
        "task_started",
        "provider_create_retry",
        "provider_create_retry",
        "provider_created",
        "provider_completed",
    ]
    assert retries == [1, 2]
    assert all(record.duration_ms >= 0 for record in lifecycle)
