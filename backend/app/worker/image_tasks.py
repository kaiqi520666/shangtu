import asyncio
import logging
import time

import httpx

from app.core.generated_media_storage import materialize_to_oss
from app.core.providers.toapis_provider import (
    MAX_WAIT_SECONDS,
    POLL_INTERVAL_SECONDS,
    TOAPIS_KEY,
    TOAPIS_STATUS_DONE,
    TOAPIS_STATUS_FAILED,
    build_create_payload,
    create_generation,
    extract_provider_error,
    extract_provider_progress,
    extract_provider_status,
    extract_provider_task_id,
    extract_result_url,
    fetch_generation,
    validate_size,
)
from app.core.task_state import set_task_progress, set_task_result, set_task_status
from app.worker.task_failures import mark_failed, mark_timeout
from app.worker.task_state_sync import fetch_task_user_id, update_task_in_db

logger = logging.getLogger("app.worker.image_tasks")


async def _set_progress(redis, task_id: str, value: int) -> None:
    await set_task_progress(redis, "image", task_id, value)


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
            await mark_failed(redis, task_id, "TOAPIS_KEY 未配置，无法调用生图服务")
            return

        user_id = await fetch_task_user_id(task_id)
        if not user_id:
            await mark_failed(redis, task_id, "任务不存在或已删除")
            return

        validation_error = validate_size(ratio, resolution)
        if validation_error:
            await mark_failed(redis, task_id, validation_error)
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
                await mark_failed(redis, task_id, f"创建 ToAPIS 任务失败: {e}")
                return
            except ValueError as e:
                await mark_failed(redis, task_id, f"ToAPIS 创建响应解析失败: {e}")
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
                await mark_failed(redis, task_id, err)
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
                await mark_timeout(redis, task_id, "等待 ToAPIS 任务超时")
                return

            if final_status == "failed" or not final_url:
                await mark_failed(
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
                await mark_failed(redis, task_id, f"下载生成图失败: {e}")
                return
            except Exception as e:
                logger.exception(
                    "OSS 上传失败: %s",
                    e,
                    extra={"task_id": task_id, "media_type": "image"},
                )
                await mark_failed(redis, task_id, f"OSS 上传失败: {e}")
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
        await mark_timeout(redis, task_id, "请求 ToAPIS 超时")
    except Exception as e:
        logger.exception(
            "任务失败详细错误: %s",
            e,
            extra={"task_id": task_id, "media_type": "image"},
        )
        await mark_failed(redis, task_id, str(e))
