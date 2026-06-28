import asyncio
import logging
import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv
from sqlalchemy import select, update

from app.core.database import SessionLocal
from app.core.generated_media_storage import materialize_to_oss, materialize_video_to_oss
from app.core.providers.toapis_provider import (
    MAX_WAIT_SECONDS,
    POLL_INTERVAL_SECONDS,
    TOAPIS_KEY,
    TOAPIS_STATUS_DONE,
    TOAPIS_STATUS_FAILED,
    VIDEO_MAX_WAIT_SECONDS,
    VIDEO_POLL_INTERVAL_SECONDS,
    build_create_payload,
    build_video_create_payload,
    create_generation,
    extract_provider_error,
    extract_provider_progress,
    extract_provider_status,
    extract_provider_task_id,
    extract_result_url,
    fetch_generation,
    validate_size,
)
from app.core.task_state import set_task_error, set_task_progress, set_task_result, set_task_status

logger = logging.getLogger("app.worker.tasks")

load_dotenv()

# 主动剥离代理环境变量，防止 Windows 走代理失败
for _proxy_key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(_proxy_key, None)


def _task_model(media_type: str):
    from app.models import ImageTask, VideoTask

    return ImageTask if media_type == "image" else VideoTask


async def update_generation_task_in_db(
    media_type: str,
    task_id: str,
    *,
    status: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    provider_task_id: str | None = None,
) -> None:
    model = _task_model(media_type)

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
            update(model)
            .where(model.id == task_id)
            .values(**values)
        )
        await session.commit()


async def update_task_in_db(
    task_id: str,
    *,
    status: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    provider_task_id: str | None = None,
) -> None:
    await update_generation_task_in_db(
        "image",
        task_id,
        status=status,
        result_url=result_url,
        error_message=error_message,
        progress=progress,
        provider_task_id=provider_task_id,
    )


async def update_video_task_in_db(
    task_id: str,
    *,
    status: str | None = None,
    result_url: str | None = None,
    error_message: str | None = None,
    progress: int | None = None,
    provider_task_id: str | None = None,
) -> None:
    await update_generation_task_in_db(
        "video",
        task_id,
        status=status,
        result_url=result_url,
        error_message=error_message,
        progress=progress,
        provider_task_id=provider_task_id,
    )


async def fetch_generation_task_user_id(media_type: str, task_id: str) -> int | None:
    model = _task_model(media_type)

    async with SessionLocal() as session:
        result = await session.execute(
            select(model.user_id).where(model.id == task_id)
        )
        return result.scalar_one_or_none()


async def fetch_task_user_id(task_id: str) -> int | None:
    return await fetch_generation_task_user_id("image", task_id)


async def fetch_video_task_user_id(task_id: str) -> int | None:
    return await fetch_generation_task_user_id("video", task_id)


async def _set_progress(redis, task_id: str, value: int) -> None:
    await set_task_progress(redis, "image", task_id, value)


async def _set_video_progress(redis, task_id: str, value: int) -> None:
    await set_task_progress(redis, "video", task_id, value)


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


async def refund_generation_credit(media_type: str, task_id: str) -> bool:
    """幂等退款：按任务实际扣费退回积分，已退过直接 no-op。返回是否本次执行了退款。"""
    from app.models import User

    model = _task_model(media_type)

    async with SessionLocal() as session:
        async with session.begin():
            task_row = await session.execute(
                select(
                    model.user_id,
                    model.credit_cost,
                    model.credit_refunded,
                ).where(model.id == task_id).with_for_update()
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
                update(model).where(model.id == task_id).values(
                    credit_refunded=True
                )
            )
    return True


async def refund_task_credit(task_id: str) -> bool:
    return await refund_generation_credit("image", task_id)


async def refund_video_task_credit(task_id: str) -> bool:
    return await refund_generation_credit("video", task_id)


async def _mark_terminal(
    redis,
    media_type: str,
    task_id: str,
    raw_message: str,
    *,
    status: str,
) -> None:
    logger.warning(
        "generation %s %s (raw): %s",
        media_type,
        status,
        raw_message,
        extra={"task_id": task_id, "media_type": media_type, "status": status},
    )
    friendly = normalize_provider_error(raw_message, media_type=media_type)
    await update_generation_task_in_db(media_type, task_id, status=status, error_message=friendly)
    await refund_generation_credit(media_type, task_id)
    await set_task_error(redis, media_type, task_id, friendly)
    await set_task_status(redis, media_type, task_id, status, ttl=3600)


async def _mark_failed(redis, task_id: str, raw_message: str) -> None:
    await _mark_terminal(redis, "image", task_id, raw_message, status="failed")


async def _mark_timeout(redis, task_id: str, raw_message: str) -> None:
    await _mark_terminal(redis, "image", task_id, raw_message, status="timeout")


async def _mark_video_failed(redis, task_id: str, raw_message: str) -> None:
    await _mark_terminal(redis, "video", task_id, raw_message, status="failed")


async def _mark_video_timeout(redis, task_id: str, raw_message: str) -> None:
    await _mark_terminal(redis, "video", task_id, raw_message, status="timeout")


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
        await set_task_status(redis, "image", task_id, "processing", ttl=7200)
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
                create_result = await create_generation(
                    client,
                    media="image",
                    payload=create_payload,
                )
            except httpx.HTTPError as e:
                await _mark_failed(redis, task_id, f"创建 ToAPIS 任务失败: {e}")
                return
            except ValueError as e:
                await _mark_failed(redis, task_id, f"ToAPIS 创建响应解析失败: {e}")
                return

            logger.debug(
                "toapis 创建响应: %s",
                create_result,
                extra={"task_id": task_id, "media_type": "image"},
            )

            provider_task_id = extract_provider_task_id(create_result)
            if not provider_task_id:
                err = (
                    extract_provider_error(create_result)
                    or "ToAPIS 未返回 task id"
                )
                await _mark_failed(redis, task_id, err)
                return

            await update_task_in_db(task_id, provider_task_id=provider_task_id)

            deadline = time.monotonic() + MAX_WAIT_SECONDS
            final_status: str | None = None
            final_url: str | None = None
            final_error: str | None = None

            while time.monotonic() < deadline:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                try:
                    poll_result = await fetch_generation(
                        client,
                        media="image",
                        provider_task_id=provider_task_id,
                    )
                except httpx.HTTPError as e:
                    logger.warning(
                        "轮询 ToAPIS 异常: %s",
                        e,
                        extra={
                            "task_id": task_id,
                            "media_type": "image",
                            "provider_task_id": provider_task_id,
                        },
                    )
                    continue
                except ValueError as e:
                    logger.warning(
                        "ToAPIS 轮询响应解析失败: %s",
                        e,
                        extra={
                            "task_id": task_id,
                            "media_type": "image",
                            "provider_task_id": provider_task_id,
                        },
                    )
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
                logger.exception(
                    "OSS 上传失败: %s",
                    e,
                    extra={"task_id": task_id, "media_type": "image"},
                )
                await _mark_failed(redis, task_id, f"OSS 上传失败: {e}")
                return

        # 先 DB 后 Redis：避免 status=done 但 result_url=null 竞态
        await update_task_in_db(
            task_id,
            status="done",
            result_url=uploaded.url,
            progress=100,
        )
        await set_task_result(redis, "image", task_id, uploaded.url)
        await _set_progress(redis, task_id, 100)
        await set_task_status(redis, "image", task_id, "done", ttl=86400)

    except httpx.TimeoutException:
        await _mark_timeout(redis, task_id, "请求 ToAPIS 超时")
    except Exception as e:
        logger.exception(
            "任务失败详细错误: %s",
            e,
            extra={"task_id": task_id, "media_type": "image"},
        )
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
        await set_task_status(redis, "video", task_id, "processing", ttl=7200)
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
                create_result = await create_generation(
                    client,
                    media="video",
                    payload=create_payload,
                )
            except httpx.HTTPError as e:
                detail = ""
                resp = getattr(e, "response", None)
                if resp is not None:
                    try:
                        detail = (resp.text or "")[:500]
                    except Exception:
                        detail = ""
                    logger.warning(
                        "toapis 视频创建失败 status=%s body=%s",
                        resp.status_code,
                        detail,
                        extra={"task_id": task_id, "media_type": "video"},
                    )
                    reason = f"{e} | {detail}" if detail else str(e)
                else:
                    reason = f"{type(e).__name__}: {e!r}"
                    logger.warning(
                        "toapis 视频创建传输层错误 %s",
                        reason,
                        extra={"task_id": task_id, "media_type": "video"},
                    )
                await _mark_video_failed(
                    redis,
                    task_id,
                    f"创建 ToAPIS 视频任务失败: {reason}",
                )
                return
            except ValueError as e:
                await _mark_video_failed(redis, task_id, f"ToAPIS 视频创建响应解析失败: {e}")
                return

            logger.debug(
                "toapis 视频创建响应: %s",
                create_result,
                extra={"task_id": task_id, "media_type": "video"},
            )

            provider_task_id = extract_provider_task_id(create_result)
            if not provider_task_id:
                err = (
                    extract_provider_error(create_result)
                    or "ToAPIS 未返回 video task id"
                )
                await _mark_video_failed(redis, task_id, err)
                return

            await update_video_task_in_db(task_id, provider_task_id=provider_task_id)

            deadline = time.monotonic() + VIDEO_MAX_WAIT_SECONDS
            final_status: str | None = None
            final_url: str | None = None
            final_error: str | None = None

            while time.monotonic() < deadline:
                await asyncio.sleep(VIDEO_POLL_INTERVAL_SECONDS)
                try:
                    poll_result = await fetch_generation(
                        client,
                        media="video",
                        provider_task_id=provider_task_id,
                    )
                except httpx.HTTPError as e:
                    logger.warning(
                        "轮询 ToAPIS 视频异常: %s",
                        e,
                        extra={
                            "task_id": task_id,
                            "media_type": "video",
                            "provider_task_id": provider_task_id,
                        },
                    )
                    continue
                except ValueError as e:
                    logger.warning(
                        "ToAPIS 视频轮询响应解析失败: %s",
                        e,
                        extra={
                            "task_id": task_id,
                            "media_type": "video",
                            "provider_task_id": provider_task_id,
                        },
                    )
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
                logger.exception(
                    "视频上传 OSS 失败: %s",
                    e,
                    extra={"task_id": task_id, "media_type": "video"},
                )
                await _mark_video_failed(redis, task_id, f"视频上传 OSS 失败: {e}")
                return

        await update_video_task_in_db(
            task_id,
            status="done",
            result_url=uploaded.url,
            progress=100,
        )
        await set_task_result(redis, "video", task_id, uploaded.url)
        await _set_video_progress(redis, task_id, 100)
        await set_task_status(redis, "video", task_id, "done", ttl=86400)

    except httpx.TimeoutException:
        await _mark_video_timeout(redis, task_id, "请求 ToAPIS 视频服务超时")
    except Exception as e:
        logger.exception(
            "视频任务失败详细错误: %s",
            e,
            extra={"task_id": task_id, "media_type": "video"},
        )
        await _mark_video_failed(redis, task_id, str(e))
