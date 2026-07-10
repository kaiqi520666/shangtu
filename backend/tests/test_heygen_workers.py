from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

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
