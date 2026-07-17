import logging

import pytest

from app.core.sse import text_streaming_response


async def content_stream(*items):
    for item in items:
        if isinstance(item, Exception):
            raise item
        yield item


async def response_body(response) -> str:
    chunks = [chunk async for chunk in response.body_iterator]
    return b"".join(chunk if isinstance(chunk, bytes) else chunk.encode() for chunk in chunks).decode()


@pytest.mark.asyncio
async def test_text_streaming_response_emits_delta_and_done_events():
    response = text_streaming_response(
        content_stream("你好", "世界"),
        logger=logging.getLogger("test.sse"),
        error_log="stream failed",
        error_message="生成失败",
    )

    body = await response_body(response)

    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    assert 'event: delta\ndata: {"content":"你好"}' in body
    assert body.endswith("event: done\ndata: {}\n\n")


@pytest.mark.asyncio
async def test_text_streaming_response_hides_internal_errors():
    response = text_streaming_response(
        content_stream("部分", RuntimeError("private provider response")),
        logger=logging.getLogger("test.sse"),
        error_log="stream failed",
        error_message="生成失败，请稍后重试",
    )

    body = await response_body(response)

    assert 'event: error\ndata: {"message":"生成失败，请稍后重试"}' in body
    assert "private provider response" not in body
