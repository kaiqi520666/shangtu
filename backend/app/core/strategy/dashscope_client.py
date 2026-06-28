import os

import httpx
from dotenv import load_dotenv

from app.core.model_config import QWEN_TEXT_MODEL
from app.core.strategy.parsing import _parse_json_response
from app.core.strategy.prompts import (
    MULTI_IMAGE_ANALYSIS_RULE,
    build_free_image_optimize_prompt,
    build_free_video_optimize_prompt,
    build_multimodal_image_content,
    build_product_prompt,
)

load_dotenv()


class DashScopeConfigError(RuntimeError):
    pass


def get_dashscope_endpoint() -> str:
    base_url = os.getenv("DASHSCOPE_URL")
    if not base_url:
        raise DashScopeConfigError("DASHSCOPE_URL未配置")

    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def get_dashscope_api_key() -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise DashScopeConfigError("DASHSCOPE_API_KEY未配置")
    return api_key


async def analyze_product_image(
    *,
    images: list[dict],
    platform: str = "",
    prompt: str | None = None,
) -> str:
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

    async with httpx.AsyncClient(timeout=60) as client:
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

    return content.strip()


async def optimize_free_image_prompt(prompt: str) -> str:
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

    async with httpx.AsyncClient(timeout=60) as client:
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

    return content.strip()


async def optimize_free_video_prompt(prompt: str) -> str:
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

    async with httpx.AsyncClient(timeout=60) as client:
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

    return content.strip()


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
