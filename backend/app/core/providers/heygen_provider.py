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
    script: str,
    voice_id: str,
    engine_type: str,
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
        "script": script,
        "voice_id": voice_id,
        "engine": {"type": engine_type},
    }
    if voice_settings:
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
