import json
from collections.abc import AsyncIterator
from unittest.mock import patch

import pytest

from app.core.strategy import dashscope_client


def frame(data: dict | str) -> bytes:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"data: {payload}\n\n".encode()


async def byte_chunks(*chunks: bytes) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


class FakeResponse:
    def __init__(self, chunks, status_code=200):
        self.chunks = chunks
        self.status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def aiter_bytes(self):
        return byte_chunks(*self.chunks)


class FakeClient:
    def __init__(self, response, requests):
        self.response = response
        self.requests = requests

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def stream(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        return self.response


async def collect_stream(chunks, status_code=200):
    requests = []
    response = FakeResponse(chunks, status_code)
    with (
        patch.object(dashscope_client, "get_dashscope_endpoint", return_value="https://provider.test"),
        patch.object(dashscope_client, "get_dashscope_api_key", return_value="secret"),
        patch.object(
            dashscope_client.httpx,
            "AsyncClient",
            return_value=FakeClient(response, requests),
        ),
    ):
        content = [item async for item in dashscope_client._stream_dashscope_content({"model": "test"})]
    return content, requests


@pytest.mark.asyncio
async def test_stream_parser_handles_arbitrary_utf8_chunks_and_merged_frames():
    raw = b"".join(
        [
            frame({"choices": [{"delta": {"content": "你好"}}]}),
            frame({"choices": [{"delta": {"content": "世界"}}]}),
            frame("[DONE]"),
        ]
    )
    split = raw.index("你".encode()) + 1

    content, requests = await collect_stream([raw[:split], raw[split:]])

    assert content == ["你好", "世界"]
    assert requests[0][2]["json"]["stream"] is True


@pytest.mark.asyncio
async def test_stream_ignores_usage_frame_before_done():
    chunks = [
        frame({"choices": [{"delta": {"content": "完整内容"}}]}),
        frame({"choices": [], "usage": {"total_tokens": 12}}),
        frame("[DONE]"),
    ]

    content, _requests = await collect_stream(chunks)

    assert content == ["完整内容"]


@pytest.mark.asyncio
async def test_stream_rejects_upstream_http_error_without_response_body():
    with pytest.raises(RuntimeError, match="DashScope请求失败: 503") as exc_info:
        await collect_stream([b"private provider response"], status_code=503)

    assert "private provider response" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_stream_rejects_malformed_events():
    with pytest.raises(RuntimeError, match="流式响应格式异常"):
        await collect_stream([frame("not-json")])


@pytest.mark.asyncio
async def test_stream_rejects_empty_choices_without_usage():
    with pytest.raises(RuntimeError, match="流式响应格式异常"):
        await collect_stream([frame({"choices": []})])


@pytest.mark.asyncio
async def test_stream_requires_done_after_partial_content():
    chunks = [frame({"choices": [{"delta": {"content": "部分内容"}}]})]

    with pytest.raises(RuntimeError, match="未正常结束"):
        await collect_stream(chunks)


@pytest.mark.asyncio
async def test_closing_stream_closes_upstream_iterator():
    closed = False

    async def tracked_chunks():
        nonlocal closed
        try:
            yield frame({"choices": [{"delta": {"content": "第一段"}}]})
            yield frame("[DONE]")
        finally:
            closed = True

    response = FakeResponse([])
    response.aiter_bytes = tracked_chunks
    with (
        patch.object(dashscope_client, "get_dashscope_endpoint", return_value="https://provider.test"),
        patch.object(dashscope_client, "get_dashscope_api_key", return_value="secret"),
        patch.object(
            dashscope_client.httpx,
            "AsyncClient",
            return_value=FakeClient(response, []),
        ),
    ):
        stream = dashscope_client._stream_dashscope_content({"model": "test"})
        assert await anext(stream) == "第一段"
        await stream.aclose()

    assert closed is True
