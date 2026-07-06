from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

HEYGEN_BASE_URL = (os.getenv("HEYGEN_BASE_URL") or "https://api.heygen.com").rstrip("/")
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
AVATAR_PAGE_SIZE = 20
VOICE_PAGE_SIZE = 100


class HeygenConfigError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    if not HEYGEN_API_KEY:
        raise HeygenConfigError("HEYGEN_API_KEY 未配置，无法同步系统数字人和声音")
    return {"x-api-key": HEYGEN_API_KEY}


def _request_headers(idempotency_key: str | None = None) -> dict[str, str]:
    headers = _headers()
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


async def _fetch_page(
    client: httpx.AsyncClient,
    *,
    path: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    response = await client.get(
        f"{HEYGEN_BASE_URL}{path}",
        headers=_headers(),
        params=params,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("HeyGen 返回格式不正确")
    return payload


def parse_heygen_error_message(exc: httpx.HTTPError) -> str:
    response = getattr(exc, "response", None)
    if response is None:
        return "HeyGen 请求失败，请稍后重试"
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = str(error.get("message") or "").strip()
            if message:
                return message
        message = str(payload.get("message") or "").strip()
        if message:
            return message
    if response.status_code == 401:
        return "HeyGen API Key 无效或已失效"
    if response.status_code == 404:
        return "HeyGen 任务不存在"
    if response.status_code == 409:
        return "HeyGen 任务正在处理中，请稍后重试"
    if response.status_code == 429:
        return "HeyGen 请求过于频繁，请稍后重试"
    return "HeyGen 请求失败，请稍后重试"


async def create_avatar_video(
    client: httpx.AsyncClient,
    *,
    avatar_id: str,
    title: str,
    aspect_ratio: str,
    resolution: str,
    script: str | None = None,
    voice_id: str | None = None,
    audio_url: str | None = None,
    engine_type: str,
    background_url: str | None = None,
    voice_settings: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "avatar",
        "avatar_id": avatar_id,
        "title": title,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "output_format": "mp4",
        "engine": {"type": engine_type},
    }
    if audio_url:
        payload["audio_url"] = audio_url
    else:
        if script:
            payload["script"] = script
        if voice_id:
            payload["voice_id"] = voice_id
    if background_url:
        payload["background"] = {"type": "image", "url": background_url}
    if voice_settings and not audio_url:
        payload["voice_settings"] = voice_settings
    response = await client.post(
        f"{HEYGEN_BASE_URL}/v3/videos",
        headers=_request_headers(idempotency_key),
        json=payload,
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError("HeyGen 创建视频返回格式不正确")
    return body["data"]


async def create_photo_avatar(
    client: httpx.AsyncClient,
    *,
    name: str,
    image_url: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    payload = {
        "name": name,
        "type": "photo",
        "file": {
            "type": "url",
            "url": image_url,
        },
    }
    response = await client.post(
        f"{HEYGEN_BASE_URL}/v3/avatars",
        headers=_request_headers(idempotency_key),
        json=payload,
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError("HeyGen 创建照片数字人返回格式不正确")
    return body["data"]


async def list_translation_languages(client: httpx.AsyncClient) -> list[str]:
    response = await client.get(
        f"{HEYGEN_BASE_URL}/v3/video-translations/languages",
        headers=_request_headers(),
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError("HeyGen 翻译语言返回格式不正确")
    languages = body["data"].get("languages")
    if not isinstance(languages, list):
        raise ValueError("HeyGen 翻译语言缺少 data.languages")
    return [str(item).strip() for item in languages if str(item or "").strip()]


async def create_video_translation(
    client: httpx.AsyncClient,
    *,
    video_url: str,
    title: str,
    output_language: str,
    mode: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    payload = {
        "video_url": video_url,
        "title": title,
        "output_languages": [output_language],
        "mode": mode,
        "translate_audio_only": False,
    }
    response = await client.post(
        f"{HEYGEN_BASE_URL}/v3/video-translations",
        headers=_request_headers(idempotency_key),
        json=payload,
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError("HeyGen 创建视频翻译返回格式不正确")
    return body["data"]


async def get_video_translation(
    client: httpx.AsyncClient,
    *,
    video_translation_id: str,
) -> dict[str, Any]:
    response = await client.get(
        f"{HEYGEN_BASE_URL}/v3/video-translations/{video_translation_id}",
        headers=_request_headers(),
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError("HeyGen 视频翻译详情返回格式不正确")
    return body["data"]


async def get_avatar_look(
    client: httpx.AsyncClient,
    *,
    avatar_look_id: str,
) -> dict[str, Any]:
    response = await client.get(
        f"{HEYGEN_BASE_URL}/v3/avatars/looks/{avatar_look_id}",
        headers=_request_headers(),
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError("HeyGen 照片数字人详情返回格式不正确")
    return body["data"]


async def get_video(
    client: httpx.AsyncClient,
    *,
    video_id: str,
) -> dict[str, Any]:
    response = await client.get(
        f"{HEYGEN_BASE_URL}/v3/videos/{video_id}",
        headers=_request_headers(),
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        raise ValueError("HeyGen 视频详情返回格式不正确")
    return body["data"]


def _is_terminal_token_error(exc: httpx.HTTPStatusError, token: str) -> bool:
    return bool(token) and exc.response.status_code == 400


async def iter_public_studio_avatar_looks(
    client: httpx.AsyncClient,
) -> AsyncIterator[dict[str, Any]]:
    token = ""
    while True:
        params = (
            {
                "token": token,
                "avatar_type": "studio_avatar",
                "ownership": "public",
            }
            if token
            else {
                "avatar_type": "studio_avatar",
                "ownership": "public",
                "limit": AVATAR_PAGE_SIZE,
            }
        )
        try:
            payload = await _fetch_page(client, path="/v3/avatars/looks", params=params)
        except httpx.HTTPStatusError as exc:
            if _is_terminal_token_error(exc, token):
                return
            raise
        items = payload.get("data")
        if not isinstance(items, list):
            raise ValueError("HeyGen 数字人列表缺少 data")
        for item in items:
            if (
                isinstance(item, dict)
                and str(item.get("avatar_type") or "").strip() == "studio_avatar"
            ):
                yield item
        if not payload.get("has_more"):
            return
        token = str(payload.get("next_token") or "").strip()
        if not token:
            return


async def iter_public_voices(
    client: httpx.AsyncClient,
) -> AsyncIterator[dict[str, Any]]:
    token = ""
    while True:
        params = {"token": token} if token else {"type": "public", "limit": VOICE_PAGE_SIZE}
        try:
            payload = await _fetch_page(client, path="/v3/voices", params=params)
        except httpx.HTTPStatusError as exc:
            if _is_terminal_token_error(exc, token):
                return
            raise
        items = payload.get("data")
        if not isinstance(items, list):
            raise ValueError("HeyGen 声音列表缺少 data")
        for item in items:
            if isinstance(item, dict) and str(item.get("type") or "").strip() == "public":
                yield item
        if not payload.get("has_more"):
            return
        token = str(payload.get("next_token") or "").strip()
        if not token:
            return
