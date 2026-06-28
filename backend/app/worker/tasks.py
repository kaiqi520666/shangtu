import asyncio
import json
import os
import time
import traceback
from typing import Any

import httpx
from dotenv import load_dotenv
from sqlalchemy import select, update

from app.core.database import SessionLocal
from app.core.model_config import IMAGE_GENERATE_MODEL, VIDEO_GENERATE_MODEL
from app.core.oss import ALLOWED_IMAGE_TYPES, ALLOWED_VIDEO_TYPES, upload_image_bytes, upload_video_bytes

load_dotenv()

TOAPIS_BASE_URL = (os.getenv("TOAPIS_URL") or "https://toapis.com").rstrip("/")
TOAPIS_KEY = os.getenv("TOAPIS_KEY")

# 主动剥离代理环境变量，防止 Windows 走代理失败
for _proxy_key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(_proxy_key, None)

DEFAULT_GENERATED_CONTENT_TYPE = "image/png"
DEFAULT_GENERATED_VIDEO_CONTENT_TYPE = "video/mp4"

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
TOAPIS_STATUS_FAILED = {"failed", "error", "cancelled", "canceled"}


async def update_task_in_db(
    task_id: str,
    *,
    status: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    provider_task_id: str | None = None,
) -> None:
    from app.models import ImageTask

    values: dict[str, Any] = {}
    if status is not None:
        values["status"] = status
    if result_url is not None:
        values["result_url"] = result_url
    if error_message is not None:
        values["error_message"] = error_message
    if progress is not None:
        values["progress"] = max(0, min(100, int(progress)))
    if provider_task_id is not None:
        values["provider_task_id"] = provider_task_id

    if not values:
        return

    async with SessionLocal() as session:
        await session.execute(
            update(ImageTask)
            .where(ImageTask.id == task_id)
            .values(**values)
        )
        await session.commit()


async def update_video_task_in_db(
    task_id: str,
    *,
    status: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    provider_task_id: str | None = None,
) -> None:
    from app.models import VideoTask

    values: dict[str, Any] = {}
    if status is not None:
        values["status"] = status
    if result_url is not None:
        values["result_url"] = result_url
    if error_message is not None:
        values["error_message"] = error_message
    if progress is not None:
        values["progress"] = max(0, min(100, int(progress)))
    if provider_task_id is not None:
        values["provider_task_id"] = provider_task_id

    if not values:
        return

    async with SessionLocal() as session:
        await session.execute(
            update(VideoTask)
            .where(VideoTask.id == task_id)
            .values(**values)
        )
        await session.commit()


async def fetch_task_user_id(task_id: str) -> int | None:
    from app.models import ImageTask

    async with SessionLocal() as session:
        result = await session.execute(
            select(ImageTask.user_id).where(ImageTask.id == task_id)
        )
        return result.scalar_one_or_none()


async def fetch_video_task_user_id(task_id: str) -> int | None:
    from app.models import VideoTask

    async with SessionLocal() as session:
        result = await session.execute(
            select(VideoTask.user_id).where(VideoTask.id == task_id)
        )
        return result.scalar_one_or_none()


def validate_size(ratio: str, resolution: str) -> str | None:
    """校验 (ratio, resolution) 是否被 ToAPIS 支持，不支持时返回中文错误说明，否则返回 None。"""
    if ratio not in TOAPIS_SIZE_TABLE:
        return f"不支持的图片比例：{ratio}"
    if resolution not in TOAPIS_SIZE_TABLE[ratio]:
        supported = "/".join(TOAPIS_SIZE_TABLE[ratio].keys())
        return f"当前比例 {ratio} 不支持 {resolution}，请选择 {supported}"
    return None


def normalize_content_type(raw: str | None) -> str:
    if not raw:
        return DEFAULT_GENERATED_CONTENT_TYPE
    main = raw.split(";", 1)[0].strip().lower()
    if main == "image/jpg":
        main = "image/jpeg"
    if main in ALLOWED_IMAGE_TYPES:
        return main
    return DEFAULT_GENERATED_CONTENT_TYPE


def normalize_video_content_type(raw: str | None, url: str | None = None) -> str:
    if raw:
        main = raw.split(";", 1)[0].strip().lower()
        if main in ALLOWED_VIDEO_TYPES:
            return main
    url_lower = (url or "").lower()
    if url_lower.endswith(".webm"):
        return "video/webm"
    if url_lower.endswith(".mov"):
        return "video/quicktime"
    if url_lower.endswith(".mkv"):
        return "video/x-matroska"
    return DEFAULT_GENERATED_VIDEO_CONTENT_TYPE


def build_create_payload(
    *,
    prompt: str,
    ratio: str,
    resolution: str,
    image_urls: list[str] | None = None,
) -> dict:
    reference_urls = [url for url in (image_urls or []) if url]
    payload: dict[str, Any] = {
        "model": IMAGE_GENERATE_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": ratio,
        "resolution": resolution,
        "response_format": "url",
    }
    if reference_urls:
        payload["image_urls"] = reference_urls
    return payload


def build_video_create_payload(
    *,
    prompt: str,
    action: str,
    duration: int,
    aspect_ratio: str,
    resolution: str,
    image_urls: list[str],
    client_business_id: str | None = None,
) -> dict:
    cleaned_urls = [url for url in image_urls if url]
    provider_resolution = str(resolution or "").upper()
    payload: dict[str, Any] = {
        "model": VIDEO_GENERATE_MODEL,
        "action": action,
        "prompt": prompt,
        "duration": int(duration),
        "aspect_ratio": aspect_ratio,
        "resolution": provider_resolution,
        "watermark": False,
    }
    if action == "image-to-video":
        payload["image_urls"] = cleaned_urls[:1]
    else:
        payload["reference_images"] = cleaned_urls[:9]
    if client_business_id:
        payload["client_business_id"] = client_business_id
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


def extract_provider_error(poll_response: dict) -> str | None:
    err = poll_response.get("error") or poll_response.get("error_message")
    if isinstance(err, dict):
        err = err.get("message") or err.get("detail")
    if isinstance(err, str) and err:
        return err
    data = poll_response.get("data")
    if isinstance(data, dict):
        nested = data.get("error") or data.get("error_message")
        if isinstance(nested, dict):
            nested = nested.get("message") or nested.get("detail")
        if isinstance(nested, str) and nested:
            return nested
    return None


def extract_result_url(poll_response: dict) -> str | None:
    # 候选位置：顶层 data / 顶层 result / data.data / data.result（覆盖 ToAPIS 的多种返回形态）
    candidates: list[Any] = [
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


async def materialize_to_oss(
    *,
    user_id: int,
    url: str,
    client: httpx.AsyncClient,
):
    download = await client.get(url)
    download.raise_for_status()
    content_bytes = download.content
    content_type = normalize_content_type(download.headers.get("content-type"))

    return await upload_image_bytes(
        user_id=user_id,
        content=content_bytes,
        content_type=content_type,
        source="generated",
    )


async def materialize_video_to_oss(
    *,
    user_id: int,
    url: str,
    client: httpx.AsyncClient,
):
    download = await client.get(url)
    download.raise_for_status()
    content_bytes = download.content
    content_type = normalize_video_content_type(
        download.headers.get("content-type"),
        url,
    )

    return await upload_video_bytes(
        user_id=user_id,
        content=content_bytes,
        content_type=content_type,
        source="generated-videos",
    )


async def _set_progress(redis, task_id: str, value: int) -> None:
    await redis.set(
        f"task:{task_id}:progress", str(max(0, min(100, value))), ex=7200
    )


async def _set_video_progress(redis, task_id: str, value: int) -> None:
    await redis.set(
        f"video_task:{task_id}:progress", str(max(0, min(100, value))), ex=7200
    )


PROVIDER_ERROR_COPY = {
    "image": {
        "default": "生图失败，请调整提示词后重试。",
        "unsafe": "生成内容触发平台安全策略，请尝试减少敏感词、夸张功效、品牌/认证/人物相关描述后重新生成。",
        "rate_limit": "生图服务繁忙，请稍后再试。",
        "timeout": "生图任务超时，请稍后重试。",
        "upstream": "上游生图服务暂时失败，请稍后重试。",
    },
    "video": {
        "default": "视频生成失败，请调整提示词或参考图后重试。",
        "unsafe": "视频内容触发平台安全策略，请减少敏感词、夸张功效、品牌/认证/人物相关描述后重新生成。",
        "rate_limit": "视频生成服务繁忙，请稍后再试。",
        "timeout": "视频生成任务超时，请稍后重试。",
        "upstream": "上游视频生成服务暂时失败，请稍后重试。",
    },
}

PROVIDER_ERROR_RULES = [
    ("unsafe", ("image_unsafe", "unsafe")),
    ("rate_limit", ("rate limit", "too many requests", "429")),
    ("timeout", ("timeout", "timed out")),
    ("upstream", ("upstream api failed", "upstream")),
]


def normalize_provider_error(message: str | None, media_type: str = "image") -> str:
    """把上游 / 第三方原始错误归一化为对用户友好的中文文案；技术原文交给日志。

    规则：
    1. 命中 image_unsafe / 上游 API failed / timeout / rate limit 等关键词 → 对应固定文案
    2. 不命中关键词、但消息包含中文 → 直接保留（属于我们自己写的中文错误，如 "OSS 上传失败: xxx"）
    3. 都不命中 → 兜底文案，避免把上游英文 JSON 暴露给用户
    """
    copy = PROVIDER_ERROR_COPY.get(media_type) or PROVIDER_ERROR_COPY["image"]
    if not message:
        return copy["default"]
    lower = message.lower()
    for error_type, keywords in PROVIDER_ERROR_RULES:
        if any(keyword in lower for keyword in keywords):
            return copy[error_type]
    if "超时" in message:
        return copy["timeout"]
    if any("一" <= ch <= "鿿" for ch in message):
        return message
    return copy["default"]


async def refund_task_credit(task_id: str) -> bool:
    """幂等退款：按任务实际扣费退回积分，已退过直接 no-op。返回是否本次执行了退款。"""
    from app.models import ImageTask, User

    async with SessionLocal() as session:
        async with session.begin():
            task_row = await session.execute(
                select(
                    ImageTask.user_id,
                    ImageTask.credit_cost,
                    ImageTask.credit_refunded,
                ).where(ImageTask.id == task_id).with_for_update()
            )
            row = task_row.first()
            if not row:
                return False
            user_id, credit_cost, refunded = row
            if refunded:
                return False
            refund_amount = max(1, int(credit_cost or 1))
            await session.execute(
                update(User).where(User.id == user_id).values(
                    credits=User.credits + refund_amount
                )
            )
            await session.execute(
                update(ImageTask).where(ImageTask.id == task_id).values(
                    credit_refunded=True
                )
            )
    return True


async def refund_video_task_credit(task_id: str) -> bool:
    """幂等退款：按视频任务实际扣费退回积分，已退过直接 no-op。"""
    from app.models import User, VideoTask

    async with SessionLocal() as session:
        async with session.begin():
            task_row = await session.execute(
                select(
                    VideoTask.user_id,
                    VideoTask.credit_cost,
                    VideoTask.credit_refunded,
                ).where(VideoTask.id == task_id).with_for_update()
            )
            row = task_row.first()
            if not row:
                return False
            user_id, credit_cost, refunded = row
            if refunded:
                return False
            refund_amount = max(1, int(credit_cost or 1))
            await session.execute(
                update(User).where(User.id == user_id).values(
                    credits=User.credits + refund_amount
                )
            )
            await session.execute(
                update(VideoTask).where(VideoTask.id == task_id).values(
                    credit_refunded=True
                )
            )
    return True


async def _mark_failed(redis, task_id: str, raw_message: str) -> None:
    print(f"[task {task_id}] failed (raw): {raw_message}")
    friendly = normalize_provider_error(raw_message)
    await update_task_in_db(task_id, status="failed", error_message=friendly)
    await refund_task_credit(task_id)
    await redis.set(f"task:{task_id}:error", friendly, ex=3600)
    await redis.set(f"task:{task_id}:status", "failed", ex=3600)


async def _mark_timeout(redis, task_id: str, raw_message: str) -> None:
    print(f"[task {task_id}] timeout (raw): {raw_message}")
    friendly = normalize_provider_error(raw_message)
    await update_task_in_db(task_id, status="timeout", error_message=friendly)
    await refund_task_credit(task_id)
    await redis.set(f"task:{task_id}:error", friendly, ex=3600)
    await redis.set(f"task:{task_id}:status", "timeout", ex=3600)


async def _mark_video_failed(redis, task_id: str, raw_message: str) -> None:
    print(f"[video task {task_id}] failed (raw): {raw_message}")
    friendly = normalize_provider_error(raw_message, media_type="video")
    await update_video_task_in_db(task_id, status="failed", error_message=friendly)
    await refund_video_task_credit(task_id)
    await redis.set(f"video_task:{task_id}:error", friendly, ex=3600)
    await redis.set(f"video_task:{task_id}:status", "failed", ex=3600)


async def _mark_video_timeout(redis, task_id: str, raw_message: str) -> None:
    print(f"[video task {task_id}] timeout (raw): {raw_message}")
    friendly = normalize_provider_error(raw_message, media_type="video")
    await update_video_task_in_db(task_id, status="timeout", error_message=friendly)
    await refund_video_task_credit(task_id)
    await redis.set(f"video_task:{task_id}:error", friendly, ex=3600)
    await redis.set(f"video_task:{task_id}:status", "timeout", ex=3600)


async def generate_image(
    ctx,
    task_id: str,
    prompt: str,
    ratio: str = "1:1",
    resolution: str = "1K",
    image_urls: list[str] | None = None,
):
    redis = ctx["redis"]

    try:
        await redis.set(f"task:{task_id}:status", "processing", ex=7200)
        await _set_progress(redis, task_id, 0)
        await update_task_in_db(task_id, status="processing", progress=0)

        if not TOAPIS_KEY:
            await _mark_failed(redis, task_id, "TOAPIS_KEY 未配置，无法调用生图服务")
            return

        user_id = await fetch_task_user_id(task_id)
        if not user_id:
            await _mark_failed(redis, task_id, "任务不存在或已删除")
            return

        validation_error = validate_size(ratio, resolution)
        if validation_error:
            await _mark_failed(redis, task_id, validation_error)
            return

        create_payload = build_create_payload(
            prompt=prompt,
            ratio=ratio,
            resolution=resolution,
            image_urls=image_urls,
        )

        transport = httpx.AsyncHTTPTransport(proxy=None)
        async with httpx.AsyncClient(timeout=60, transport=transport) as client:
            try:
                create_resp = await client.post(
                    f"{TOAPIS_BASE_URL}/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {TOAPIS_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=create_payload,
                )
                create_resp.raise_for_status()
                create_result = create_resp.json()
            except httpx.HTTPError as e:
                await _mark_failed(redis, task_id, f"创建 ToAPIS 任务失败: {e}")
                return
            except ValueError as e:
                await _mark_failed(redis, task_id, f"ToAPIS 创建响应解析失败: {e}")
                return

            print(f"toapis 创建响应: {create_result}")

            provider_task_id = extract_provider_task_id(create_result)
            if not provider_task_id:
                err = (
                    extract_provider_error(create_result)
                    or "ToAPIS 未返回 task id"
                )
                await _mark_failed(redis, task_id, err)
                return

            await update_task_in_db(task_id, provider_task_id=provider_task_id)

            poll_url = (
                f"{TOAPIS_BASE_URL}/v1/images/generations/{provider_task_id}"
            )
            deadline = time.monotonic() + MAX_WAIT_SECONDS
            final_status: str | None = None
            final_url: str | None = None
            final_error: str | None = None

            while time.monotonic() < deadline:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                try:
                    poll_resp = await client.get(
                        poll_url,
                        headers={"Authorization": f"Bearer {TOAPIS_KEY}"},
                    )
                    poll_resp.raise_for_status()
                    poll_result = poll_resp.json()
                except httpx.HTTPError as e:
                    print(f"轮询 ToAPIS 异常: {e}")
                    continue
                except ValueError as e:
                    print(f"ToAPIS 轮询响应解析失败: {e}")
                    continue

                provider_status = extract_provider_status(poll_result)
                provider_progress = extract_provider_progress(poll_result)

                if provider_progress is not None:
                    await _set_progress(redis, task_id, provider_progress)
                    await update_task_in_db(task_id, progress=provider_progress)

                if provider_status in TOAPIS_STATUS_DONE:
                    final_url = extract_result_url(poll_result)
                    if final_url:
                        final_status = "done"
                    else:
                        final_status = "failed"
                        final_error = "ToAPIS 已完成但未返回结果图 URL"
                    break

                if provider_status in TOAPIS_STATUS_FAILED:
                    final_status = "failed"
                    final_error = (
                        extract_provider_error(poll_result) or "ToAPIS 任务失败"
                    )
                    break
                # queued / in_progress / 未知状态：继续轮询
            else:
                await _mark_timeout(redis, task_id, "等待 ToAPIS 任务超时")
                return

            if final_status == "failed" or not final_url:
                await _mark_failed(
                    redis, task_id, final_error or "ToAPIS 任务失败"
                )
                return

            try:
                uploaded = await materialize_to_oss(
                    user_id=user_id,
                    url=final_url,
                    client=client,
                )
            except httpx.HTTPError as e:
                await _mark_failed(redis, task_id, f"下载生成图失败: {e}")
                return
            except Exception as e:
                traceback.print_exc()
                await _mark_failed(redis, task_id, f"OSS 上传失败: {e}")
                return

        # 先 DB 后 Redis：避免 status=done 但 result_url=null 竞态
        await update_task_in_db(
            task_id,
            status="done",
            result_url=uploaded.url,
            progress=100,
        )
        await redis.set(
            f"task:{task_id}:result",
            json.dumps({"url": uploaded.url}),
            ex=86400,
        )
        await _set_progress(redis, task_id, 100)
        await redis.set(f"task:{task_id}:status", "done", ex=86400)

    except httpx.TimeoutException:
        await _mark_timeout(redis, task_id, "请求 ToAPIS 超时")
    except Exception as e:
        print(f"任务失败详细错误: {e}")
        traceback.print_exc()
        await _mark_failed(redis, task_id, str(e))


async def generate_video(
    ctx,
    task_id: str,
    prompt: str,
    duration: int,
    aspect_ratio: str,
    resolution: str,
    action: str,
    image_urls: list[str],
):
    redis = ctx["redis"]

    try:
        await redis.set(f"video_task:{task_id}:status", "processing", ex=7200)
        await _set_video_progress(redis, task_id, 0)
        await update_video_task_in_db(task_id, status="processing", progress=0)

        if not TOAPIS_KEY:
            await _mark_video_failed(redis, task_id, "TOAPIS_KEY 未配置，无法调用视频生成服务")
            return

        user_id = await fetch_video_task_user_id(task_id)
        if not user_id:
            await _mark_video_failed(redis, task_id, "视频任务不存在或已删除")
            return

        create_payload = build_video_create_payload(
            prompt=prompt,
            action=action,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            image_urls=image_urls,
            client_business_id=task_id,
        )

        transport = httpx.AsyncHTTPTransport(proxy=None)
        async with httpx.AsyncClient(timeout=90, transport=transport) as client:
            try:
                create_resp = await client.post(
                    f"{TOAPIS_BASE_URL}/v1/videos/generations",
                    headers={
                        "Authorization": f"Bearer {TOAPIS_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=create_payload,
                )
                create_resp.raise_for_status()
                create_result = create_resp.json()
            except httpx.HTTPError as e:
                detail = ""
                resp = getattr(e, "response", None)
                if resp is not None:
                    try:
                        detail = (resp.text or "")[:500]
                    except Exception:
                        detail = ""
                    print(f"toapis 视频创建失败 status={resp.status_code} body={detail}")
                    reason = f"{e} | {detail}" if detail else str(e)
                else:
                    reason = f"{type(e).__name__}: {e!r}"
                    print(f"toapis 视频创建传输层错误 {reason}")
                await _mark_video_failed(
                    redis,
                    task_id,
                    f"创建 ToAPIS 视频任务失败: {reason}",
                )
                return
            except ValueError as e:
                await _mark_video_failed(redis, task_id, f"ToAPIS 视频创建响应解析失败: {e}")
                return

            print(f"toapis 视频创建响应: {create_result}")

            provider_task_id = extract_provider_task_id(create_result)
            if not provider_task_id:
                err = (
                    extract_provider_error(create_result)
                    or "ToAPIS 未返回 video task id"
                )
                await _mark_video_failed(redis, task_id, err)
                return

            await update_video_task_in_db(task_id, provider_task_id=provider_task_id)

            poll_url = f"{TOAPIS_BASE_URL}/v1/videos/generations/{provider_task_id}"
            deadline = time.monotonic() + VIDEO_MAX_WAIT_SECONDS
            final_status: str | None = None
            final_url: str | None = None
            final_error: str | None = None

            while time.monotonic() < deadline:
                await asyncio.sleep(VIDEO_POLL_INTERVAL_SECONDS)
                try:
                    poll_resp = await client.get(
                        poll_url,
                        headers={"Authorization": f"Bearer {TOAPIS_KEY}"},
                    )
                    poll_resp.raise_for_status()
                    poll_result = poll_resp.json()
                except httpx.HTTPError as e:
                    print(f"轮询 ToAPIS 视频异常: {e}")
                    continue
                except ValueError as e:
                    print(f"ToAPIS 视频轮询响应解析失败: {e}")
                    continue

                provider_status = extract_provider_status(poll_result)
                provider_progress = extract_provider_progress(poll_result)

                if provider_progress is not None:
                    await _set_video_progress(redis, task_id, provider_progress)
                    await update_video_task_in_db(task_id, progress=provider_progress)

                if provider_status in TOAPIS_STATUS_DONE:
                    final_url = extract_result_url(poll_result)
                    if final_url:
                        final_status = "done"
                    else:
                        final_status = "failed"
                        final_error = "ToAPIS 已完成但未返回视频 URL"
                    break

                if provider_status in TOAPIS_STATUS_FAILED:
                    final_status = "failed"
                    final_error = (
                        extract_provider_error(poll_result) or "ToAPIS 视频任务失败"
                    )
                    break
                # queued / in_progress / 未知状态：继续轮询
            else:
                await _mark_video_timeout(redis, task_id, "等待 ToAPIS 视频任务超时")
                return

            if final_status == "failed" or not final_url:
                await _mark_video_failed(
                    redis, task_id, final_error or "ToAPIS 视频任务失败"
                )
                return

            try:
                uploaded = await materialize_video_to_oss(
                    user_id=user_id,
                    url=final_url,
                    client=client,
                )
            except httpx.HTTPError as e:
                await _mark_video_failed(redis, task_id, f"下载生成视频失败: {e}")
                return
            except Exception as e:
                traceback.print_exc()
                await _mark_video_failed(redis, task_id, f"视频上传 OSS 失败: {e}")
                return

        await update_video_task_in_db(
            task_id,
            status="done",
            result_url=uploaded.url,
            progress=100,
        )
        await redis.set(
            f"video_task:{task_id}:result",
            json.dumps({"url": uploaded.url}),
            ex=86400,
        )
        await _set_video_progress(redis, task_id, 100)
        await redis.set(f"video_task:{task_id}:status", "done", ex=86400)

    except httpx.TimeoutException:
        await _mark_video_timeout(redis, task_id, "请求 ToAPIS 视频服务超时")
    except Exception as e:
        print(f"视频任务失败详细错误: {e}")
        traceback.print_exc()
        await _mark_video_failed(redis, task_id, str(e))
