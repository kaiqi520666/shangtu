import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.routers import image_strategy, video
from app.services.llm_rate_limit import LLM_RATE_LIMIT_MESSAGE, allow_llm_request
from tests.fake_redis import FakeRedis


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("capability", "limit", "window_seconds"),
    [
        ("image-analyze", 6, 60),
        ("image-strategy", 5, 300),
        ("video-strategy", 5, 300),
        ("prompt-optimize", 15, 60),
    ],
)
async def test_llm_rate_limit_enforces_capability_rules(
    capability, limit, window_seconds
):
    redis = FakeRedis()
    key = f"llm:{capability}:7"

    for _ in range(limit):
        assert await allow_llm_request(redis, 7, capability) is True

    assert await allow_llm_request(redis, 7, capability) is False
    assert redis.expirations[key] == window_seconds


@pytest.mark.asyncio
async def test_llm_rate_limit_isolates_users():
    redis = FakeRedis()
    for _ in range(6):
        assert await allow_llm_request(redis, 7, "image-analyze") is True

    assert await allow_llm_request(redis, 7, "image-analyze") is False
    assert await allow_llm_request(redis, 8, "image-analyze") is True


@pytest.mark.asyncio
async def test_llm_rate_limit_fails_open_without_business_data(caplog):
    redis = SimpleNamespace(eval=AsyncMock(side_effect=ConnectionError("redis offline")))

    with caplog.at_level(logging.WARNING, logger="app.services.llm_rate_limit"):
        allowed = await allow_llm_request(redis, 7, "image-strategy")

    assert allowed is True
    assert "image-strategy" in caplog.text
    assert "user_id=7" in caplog.text
    assert "prompt" not in caplog.text.lower()


def request_with_redis():
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(redis_pool=FakeRedis()))
    )


@pytest.mark.asyncio
async def test_all_llm_routes_reject_before_provider_calls():
    request = request_with_redis()
    user = SimpleNamespace(id=7)
    image_limiter = AsyncMock(return_value=False)
    video_limiter = AsyncMock(return_value=False)

    with (
        patch.object(image_strategy, "allow_llm_request", image_limiter),
        patch.object(video, "allow_llm_request", video_limiter),
    ):
        responses = [
            await image_strategy.analyze_image(
                image_strategy.AnalyzeImageRequest(images=[]), request, user, object()
            ),
            await image_strategy.image_strategy(
                image_strategy.StrategyRequest(scenario="outfit", images=[]),
                request,
                user,
                object(),
            ),
            await image_strategy.free_image_optimize(
                image_strategy.FreeImageOptimizeRequest(prompt="test"), request, user
            ),
            await video.video_strategy(
                video.VideoStrategyRequest(
                    type_id="demo",
                    input_mode="reference_to_video",
                    images=[video.VideoImageItem(url="https://example.test/image.png")],
                ),
                request,
                user,
                object(),
            ),
            await video.free_video_optimize(
                video.FreeVideoOptimizeRequest(prompt="test"), request, user
            ),
        ]

    assert all(response.message == LLM_RATE_LIMIT_MESSAGE for response in responses)
    assert [call.args[2] for call in image_limiter.await_args_list] == [
        "image-analyze",
        "image-strategy",
        "prompt-optimize",
    ]
    assert [call.args[2] for call in video_limiter.await_args_list] == [
        "video-strategy",
        "prompt-optimize",
    ]


@pytest.mark.asyncio
async def test_image_route_logs_unexpected_failure(caplog):
    request = request_with_redis()
    user = SimpleNamespace(id=7)
    with (
        patch.object(image_strategy, "allow_llm_request", AsyncMock(return_value=True)),
        patch.object(image_strategy, "build_ai_write_prompt", AsyncMock(return_value="")),
        patch.object(
            image_strategy,
            "stream_product_image_analysis",
            Mock(side_effect=KeyError("unexpected")),
        ),
        caplog.at_level(logging.ERROR, logger="app.routers.image_strategy"),
    ):
        response = await image_strategy.analyze_image(
            image_strategy.AnalyzeImageRequest(images=[]), request, user, object()
        )

    assert response.message == "图片分析失败"
    assert "Unexpected image analysis failure user_id=7" in caplog.text


@pytest.mark.asyncio
async def test_video_route_logs_unexpected_failure(caplog):
    request = request_with_redis()
    user = SimpleNamespace(id=7)
    with (
        patch.object(video, "allow_llm_request", AsyncMock(return_value=True)),
        patch.object(
            video,
            "stream_free_video_prompt",
            Mock(side_effect=KeyError("unexpected")),
        ),
        caplog.at_level(logging.ERROR, logger="app.routers.video"),
    ):
        response = await video.free_video_optimize(
            video.FreeVideoOptimizeRequest(prompt="test"), request, user
        )

    assert response.message == "视频提示词优化失败"
    assert "Unexpected video prompt optimization failure user_id=7" in caplog.text
