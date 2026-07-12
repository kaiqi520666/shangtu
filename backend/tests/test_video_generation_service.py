from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.video_generation import (
    VideoGeneratePayload,
    create_video_generation_task,
)


def payload(**overrides):
    values = {
        "scenario": "product_video",
        "type_id": "product_demo",
        "title": "商品演示",
        "input_mode": "reference_to_video",
        "image_urls": ["https://example.test/product.png"],
        "input_video_url": None,
        "video_urls": [],
        "audio_urls": [],
        "user_prompt": "展示商品",
        "duration": 8,
        "resolution": "720p",
        "aspect_ratio": "9:16",
        "generate_audio": False,
        "enable_web_search": False,
        "settings_snapshot": None,
        "sort_order": 0,
        "job_id": None,
    }
    values.update(overrides)
    return VideoGeneratePayload(**values)


def database():
    return SimpleNamespace(
        add=Mock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
        execute=AsyncMock(),
    )


def prompt_result():
    return SimpleNamespace(
        final_prompt="最终视频提示词",
        prompt_snapshot={
            "system": "",
            "task": "",
            "user": "展示商品",
            "final": "最终视频提示词",
            "template_refs": [],
        },
    )


@pytest.mark.asyncio
async def test_create_video_generation_task_persists_and_enqueues():
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock())
    with (
        patch("app.services.video_generation.get_effective_video_credit_cost", AsyncMock(return_value=36)),
        patch("app.services.video_generation.build_video_generate_prompt", AsyncMock(return_value=prompt_result())),
        patch(
            "app.services.video_generation.deduct_credits_or_fail",
            AsyncMock(return_value=(SimpleNamespace(cost=36, balance_after=64), None)),
        ),
    ):
        result, failure = await create_video_generation_task(
            db=db,
            current_user=SimpleNamespace(id=7),
            payload=payload(),
            get_redis_pool=lambda: redis,
        )

    assert failure is None
    assert (result.credits, result.credit_cost) == (64, 36)
    task = db.add.call_args.args[0]
    assert (task.scenario, task.status, task.prompt) == (
        "product_video",
        "pending",
        "最终视频提示词",
    )
    redis.enqueue_job.assert_awaited_once()
    assert redis.enqueue_job.await_args.args[:2] == ("generate_video", task.id)


@pytest.mark.asyncio
async def test_create_video_generation_task_compensates_enqueue_failure():
    db = database()
    redis = SimpleNamespace(enqueue_job=AsyncMock(side_effect=RuntimeError("offline")))
    with (
        patch("app.services.video_generation.get_effective_video_credit_cost", AsyncMock(return_value=36)),
        patch("app.services.video_generation.build_video_generate_prompt", AsyncMock(return_value=prompt_result())),
        patch(
            "app.services.video_generation.deduct_credits_or_fail",
            AsyncMock(return_value=(SimpleNamespace(cost=36, balance_after=64), None)),
        ),
        patch("app.services.video_generation.refund_user_credits", AsyncMock(return_value=100)) as refund,
    ):
        result, failure = await create_video_generation_task(
            db=db,
            current_user=SimpleNamespace(id=7),
            payload=payload(),
            get_redis_pool=lambda: redis,
        )

    assert result is None
    assert failure.message == "视频任务入队失败，请稍后重试"
    assert failure.data["credits"] == 100
    refund.assert_awaited_once()
    assert db.commit.await_count == 2
