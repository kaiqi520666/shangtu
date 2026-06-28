import asyncio
import logging
import time

import httpx

from app.core.generated_media_storage import materialize_video_to_oss
from app.core.providers.toapis_provider import (
    TOAPIS_KEY,
    TOAPIS_STATUS_DONE,
    TOAPIS_STATUS_FAILED,
    VIDEO_MAX_WAIT_SECONDS,
    VIDEO_POLL_INTERVAL_SECONDS,
    build_video_create_payload,
    create_generation,
    extract_provider_error,
    extract_provider_progress,
    extract_provider_status,
    extract_provider_task_id,
    extract_result_url,
    fetch_generation,
)
from app.core.task_state import set_task_progress, set_task_result, set_task_status
from app.worker.task_failures import (
    mark_video_failed,
    mark_video_timeout,
)
from app.worker.task_state_sync import fetch_video_task_user_id, update_video_task_in_db

logger = logging.getLogger("app.worker.video_tasks")


async def _set_video_progress(redis, task_id: str, value: int) -> None:
    await set_task_progress(redis, "video", task_id, value)


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
            await mark_video_failed(redis, task_id, "TOAPIS_KEY 未配置，无法调用视频生成服务")
            return

        user_id = await fetch_video_task_user_id(task_id)
        if not user_id:
            await mark_video_failed(redis, task_id, "视频任务不存在或已删除")
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
                await mark_video_failed(
                    redis,
                    task_id,
                    f"创建 ToAPIS 视频任务失败: {reason}",
                )
                return
            except ValueError as e:
                await mark_video_failed(redis, task_id, f"ToAPIS 视频创建响应解析失败: {e}")
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
                await mark_video_failed(redis, task_id, err)
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
                await mark_video_timeout(redis, task_id, "等待 ToAPIS 视频任务超时")
                return

            if final_status == "failed" or not final_url:
                await mark_video_failed(
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
                await mark_video_failed(redis, task_id, f"下载生成视频失败: {e}")
                return
            except Exception as e:
                logger.exception(
                    "视频上传 OSS 失败: %s",
                    e,
                    extra={"task_id": task_id, "media_type": "video"},
                )
                await mark_video_failed(redis, task_id, f"视频上传 OSS 失败: {e}")
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
        await mark_video_timeout(redis, task_id, "请求 ToAPIS 视频服务超时")
    except Exception as e:
        logger.exception(
            "视频任务失败详细错误: %s",
            e,
            extra={"task_id": task_id, "media_type": "video"},
        )
        await mark_video_failed(redis, task_id, str(e))
