import os
from typing import Any

from dotenv import load_dotenv

from app.core.model_config import IMAGE_GENERATE_MODEL, VIDEO_GENERATE_MODEL

load_dotenv()

TOAPIS_BASE_URL = (os.getenv("TOAPIS_URL") or "https://toapis.com").rstrip("/")
TOAPIS_KEY = os.getenv("TOAPIS_KEY")
TOPENROUTER_BASE_URL = (
    os.getenv("TOPENROUTER_URL") or "https://tp-api.chinadatapay.com:8000"
).rstrip("/")
TOPENROUTER_KEY = os.getenv("TOPENROUTER_KEY") or os.getenv("TOPENROUTER_API_KEY")

POLL_INTERVAL_SECONDS = 5
MAX_WAIT_SECONDS = 20 * 60
VIDEO_POLL_INTERVAL_SECONDS = 10
VIDEO_MAX_WAIT_SECONDS = 40 * 60

# ToAPIS 支持的 (ratio, resolution) → 像素尺寸；与前端 frontend/src/constants/generator.js#resolutionMap 完全对齐
TOAPIS_SIZE_TABLE: dict[str, dict[str, tuple[int, int]]] = {
    "1:1": {"1K": (1024, 1024), "2K": (2048, 2048)},
    "3:2": {"1K": (1536, 1024), "2K": (2048, 1360)},
    "2:3": {"1K": (1024, 1536), "2K": (1360, 2048)},
    "4:3": {"1K": (1024, 768), "2K": (2048, 1536)},
    "3:4": {"1K": (768, 1024), "2K": (1536, 2048)},
    "5:4": {"1K": (1280, 1024), "2K": (2560, 2048)},
    "4:5": {"1K": (1024, 1280), "2K": (2048, 2560)},
    "16:9": {"1K": (1536, 864), "2K": (2048, 1152), "4K": (3840, 2160)},
    "9:16": {"1K": (864, 1536), "2K": (1152, 2048), "4K": (2160, 3840)},
    "2:1": {"1K": (2048, 1024), "2K": (2688, 1344), "4K": (3840, 1920)},
    "1:2": {"1K": (1024, 2048), "2K": (1344, 2688), "4K": (1920, 3840)},
    "21:9": {"1K": (2016, 864), "2K": (2688, 1152), "4K": (3840, 1648)},
    "9:21": {"1K": (864, 2016), "2K": (1152, 2688), "4K": (1648, 3840)},
}

TOAPIS_STATUS_DONE = {"completed", "succeeded", "success"}
TOAPIS_STATUS_FAILED = {"failed", "error", "cancelled", "canceled", "expired"}


def validate_size(ratio: str, resolution: str) -> str | None:
    """校验 (ratio, resolution) 是否被 ToAPIS 支持，不支持时返回中文错误说明，否则返回 None。"""
    if ratio not in TOAPIS_SIZE_TABLE:
        return f"不支持的图片比例：{ratio}"
    if resolution not in TOAPIS_SIZE_TABLE[ratio]:
        supported = "/".join(TOAPIS_SIZE_TABLE[ratio].keys())
        return f"当前比例 {ratio} 不支持 {resolution}，请选择 {supported}"
    return None


def build_create_payload(
    *,
    prompt: str,
    ratio: str,
    resolution: str,
    image_urls: list[str] | None = None,
) -> dict:
    reference_urls = [url for url in (image_urls or []) if url]
    provider_resolution = str(resolution or "").lower()
    payload: dict[str, Any] = {
        "model": IMAGE_GENERATE_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": ratio,
        "resolution": provider_resolution,
        "response_format": "url",
    }
    if reference_urls:
        payload["image_urls"] = reference_urls
    return payload


def build_video_create_payload(
    *,
    prompt: str,
    duration: int,
    aspect_ratio: str,
    resolution: str,
    image_urls: list[str],
    input_video_url: str | None = None,
    video_urls: list[str] | None = None,
    audio_urls: list[str] | None = None,
    generate_audio: bool = False,
    enable_web_search: bool = False,
    client_business_id: str | None = None,
) -> dict:
    cleaned_urls = [url for url in image_urls if url]
    cleaned_video_urls = [url for url in (video_urls or []) if url]
    cleaned_audio_urls = [url for url in (audio_urls or []) if url]
    provider_resolution = str(resolution or "").lower()
    content: list[dict[str, Any]] = []
    if prompt:
        content.append({"type": "text", "text": prompt})
    content.extend(
        {
            "type": "image_url",
            "image_url": {"url": url},
            "role": "reference_image",
        }
        for url in cleaned_urls[:9]
    )
    fallback_video_url = str(input_video_url or "").strip()
    if fallback_video_url and fallback_video_url not in cleaned_video_urls:
        cleaned_video_urls.append(fallback_video_url)
    for video_url in cleaned_video_urls[:3]:
        content.append(
            {
                "type": "video_url",
                "video_url": {"url": video_url},
                "role": "reference_video",
            }
        )
    for audio_url in cleaned_audio_urls[:3]:
        content.append(
            {
                "type": "audio_url",
                "audio_url": {"url": audio_url},
                "role": "reference_audio",
            }
        )
    payload: dict[str, Any] = {
        "model": VIDEO_GENERATE_MODEL,
        "content": content,
        "duration": int(duration),
        "ratio": aspect_ratio,
        "resolution": provider_resolution,
        "execution_expires_after": 3600,
        "watermark": False,
        "generate_audio": bool(generate_audio),
    }
    if enable_web_search:
        payload["tools"] = [{"type": "web_search"}]
    if client_business_id:
        payload["safety_identifier"] = client_business_id
    return payload


def extract_provider_task_id(create_response: dict) -> str | None:
    for key in ("id", "task_id", "request_id"):
        value = create_response.get(key)
        if isinstance(value, str) and value:
            return value
    data = create_response.get("data")
    if isinstance(data, dict):
        for key in ("id", "task_id"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def extract_provider_status(poll_response: dict) -> str | None:
    status = poll_response.get("status")
    if isinstance(status, str) and status:
        return status.lower()
    data = poll_response.get("data")
    if isinstance(data, dict):
        nested = data.get("status")
        if isinstance(nested, str) and nested:
            return nested.lower()
    return None


def extract_provider_progress(poll_response: dict) -> int | None:
    progress = poll_response.get("progress")
    if progress is None:
        data = poll_response.get("data")
        if isinstance(data, dict):
            progress = data.get("progress")
    if progress is None:
        return None
    try:
        return max(0, min(100, int(progress)))
    except (TypeError, ValueError):
        return None


def _extract_error_message(error: Any) -> str | None:
    if isinstance(error, dict):
        message = error.get("message") or error.get("detail")
        code = error.get("code")
        if message and code:
            return f"{code}: {message}"
        if message:
            return str(message)
        if code:
            return str(code)
    if isinstance(error, str) and error:
        return error
    return None


def extract_provider_error(poll_response: dict) -> str | None:
    err = _extract_error_message(poll_response.get("error")) or _extract_error_message(
        poll_response.get("error_message")
    )
    if err:
        return err
    data = poll_response.get("data")
    if isinstance(data, dict):
        nested = _extract_error_message(data.get("error")) or _extract_error_message(
            data.get("error_message")
        )
        if nested:
            return nested
    return None


def extract_result_url(poll_response: dict) -> str | None:
    # 候选位置：顶层 data / 顶层 result / data.data / data.result（覆盖 ToAPIS 的多种返回形态）
    candidates: list[Any] = [
        poll_response.get("content"),
        poll_response.get("data"),
        poll_response.get("result"),
    ]
    data = poll_response.get("data")
    if isinstance(data, dict):
        candidates.append(data.get("data"))
        candidates.append(data.get("result"))

    for node in candidates:
        if isinstance(node, list) and node:
            first = node[0] or {}
            url = first.get("url") if isinstance(first, dict) else None
            if isinstance(url, str) and url:
                return url
        if isinstance(node, dict):
            video_url = node.get("video_url")
            if isinstance(video_url, str) and video_url:
                return video_url
            url = node.get("url")
            if isinstance(url, str) and url:
                return url
            inner = node.get("data")
            if isinstance(inner, list) and inner:
                first = inner[0] or {}
                url = first.get("url") if isinstance(first, dict) else None
                if isinstance(url, str) and url:
                    return url
    return None


async def create_generation(client, *, media: str, payload: dict) -> dict:
    if media == "video":
        resp = await client.post(
            f"{TOPENROUTER_BASE_URL}/v1/video/tasks",
            headers={
                "Authorization": f"Bearer {TOPENROUTER_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    media_path = "images"
    resp = await client.post(
        f"{TOAPIS_BASE_URL}/v1/{media_path}/generations",
        headers={
            "Authorization": f"Bearer {TOAPIS_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


async def fetch_generation(client, *, media: str, provider_task_id: str) -> dict:
    if media == "video":
        resp = await client.get(
            f"{TOPENROUTER_BASE_URL}/v1/video/tasks/{provider_task_id}",
            headers={"Authorization": f"Bearer {TOPENROUTER_KEY}"},
        )
        resp.raise_for_status()
        return resp.json()

    media_path = "images"
    resp = await client.get(
        f"{TOAPIS_BASE_URL}/v1/{media_path}/generations/{provider_task_id}",
        headers={"Authorization": f"Bearer {TOAPIS_KEY}"},
    )
    resp.raise_for_status()
    return resp.json()
