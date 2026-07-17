import codecs
import json
from collections.abc import AsyncIterable, AsyncIterator

import httpx

from app.core.config import get_env
from app.core.model_config import QWEN_TEXT_MODEL
from app.core.strategy.parsing import _parse_json_response
from app.core.strategy.prompts import (
    MULTI_IMAGE_ANALYSIS_RULE,
    build_free_image_optimize_prompt,
    build_free_video_optimize_prompt,
    build_multimodal_image_content,
    build_product_prompt,
)

class DashScopeConfigError(RuntimeError):
    pass


def get_dashscope_endpoint() -> str:
    base_url = get_env("DASHSCOPE_URL")
    if not base_url:
        raise DashScopeConfigError("DASHSCOPE_URL未配置")

    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def get_dashscope_api_key() -> str:
    api_key = get_env("DASHSCOPE_API_KEY")
    if not api_key:
        raise DashScopeConfigError("DASHSCOPE_API_KEY未配置")
    return api_key


def stream_product_image_analysis(
    *,
    images: list[dict],
    platform: str = "",
    prompt: str | None = None,
) -> AsyncIterator[str]:
    final_prompt = "\n\n".join(
        part
        for part in [
            prompt or build_product_prompt(platform),
            MULTI_IMAGE_ANALYSIS_RULE,
        ]
        if part
    )
    content = build_multimodal_image_content(images)
    content.append({"type": "text", "text": final_prompt})

    payload = {
        "model": QWEN_TEXT_MODEL,
        "enable_thinking": False,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
    }

    return _stream_dashscope_content(payload)


def stream_free_image_prompt(prompt: str) -> AsyncIterator[str]:
    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise ValueError("请输入需要优化的提示词")

    payload = {
        "model": QWEN_TEXT_MODEL,
        "enable_thinking": False,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": build_free_image_optimize_prompt(normalized_prompt[:4000]),
                    },
                ],
            }
        ],
    }

    return _stream_dashscope_content(payload)


def stream_free_video_prompt(prompt: str) -> AsyncIterator[str]:
    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise ValueError("请输入需要优化的视频提示词")

    payload = {
        "model": QWEN_TEXT_MODEL,
        "enable_thinking": False,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": build_free_video_optimize_prompt(normalized_prompt[:4000]),
                    },
                ],
            }
        ],
    }

    return _stream_dashscope_content(payload)


async def _iter_sse_data(chunks: AsyncIterable[bytes]) -> AsyncIterator[str]:
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer = ""
    data_lines: list[str] = []
    iterator = chunks.__aiter__()

    try:
        async for chunk in iterator:
            buffer += decoder.decode(chunk)
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.rstrip("\r")
                if not line:
                    if data_lines:
                        yield "\n".join(data_lines)
                        data_lines = []
                elif line.startswith("data:"):
                    data_lines.append(line[5:].lstrip())
    finally:
        close = getattr(iterator, "aclose", None)
        if close:
            await close()

    buffer += decoder.decode(b"", final=True)
    if buffer.rstrip("\r").startswith("data:"):
        data_lines.append(buffer.rstrip("\r")[5:].lstrip())
    if data_lines:
        yield "\n".join(data_lines)


async def _stream_dashscope_content(payload: dict) -> AsyncIterator[str]:
    payload = {**payload, "stream": True}
    received_content = False
    received_done = False

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            get_dashscope_endpoint(),
            headers={"Authorization": f"Bearer {get_dashscope_api_key()}"},
            json=payload,
        ) as response:
            if response.status_code >= 400:
                raise RuntimeError(f"DashScope请求失败: {response.status_code}")

            events = _iter_sse_data(response.aiter_bytes())
            try:
                async for data in events:
                    if data == "[DONE]":
                        received_done = True
                        break
                    try:
                        event = json.loads(data)
                        content = event["choices"][0]["delta"].get("content")
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                        raise RuntimeError("DashScope流式响应格式异常") from exc
                    if isinstance(content, str) and content:
                        received_content = True
                        yield content
            finally:
                await events.aclose()

    if not received_content:
        raise RuntimeError("DashScope未返回有效内容")
    if not received_done:
        raise RuntimeError("DashScope流式响应未正常结束")


async def _request_dashscope_strategy_json(*, images: list[dict], prompt: str) -> dict:
    content = build_multimodal_image_content(images)
    content.append(
        {
            "type": "text",
            "text": "\n\n".join([prompt, MULTI_IMAGE_ANALYSIS_RULE]),
        }
    )

    payload = {
        "model": QWEN_TEXT_MODEL,
        "enable_thinking": False,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
    }

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            get_dashscope_endpoint(),
            headers={"Authorization": f"Bearer {get_dashscope_api_key()}"},
            json=payload,
        )

    if response.status_code >= 400:
        raise RuntimeError(f"DashScope请求失败: {response.status_code} {response.text[:300]}")

    result = response.json()
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("DashScope响应格式异常") from exc

    if not content or not content.strip():
        raise RuntimeError("DashScope未返回有效内容")

    return _parse_json_response(content)
