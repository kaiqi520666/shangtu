import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.providers.toapis_provider import (
    TOAPIS_KEY,
    TOAPIS_STATUS_DONE,
    TOAPIS_STATUS_FAILED,
    create_generation,
    extract_provider_error,
    extract_provider_progress,
    extract_provider_status,
    extract_provider_task_id,
    extract_result_url,
    fetch_generation,
)
from app.core.task_state import set_task_result, set_task_status

logger = logging.getLogger("app.worker.generation_runner")

SetProgressFn = Callable[[Any, str, int], Awaitable[None]]
UpdateTaskFn = Callable[..., Awaitable[None]]
FetchUserIdFn = Callable[[str], Awaitable[int | None]]
MarkTerminalFn = Callable[[Any, str, str], Awaitable[None]]
PayloadBuilderFn = Callable[[], dict[str, Any]]
MaterializeFn = Callable[..., Awaitable[Any]]
IsDownloadErrorFn = Callable[[Exception], bool]
CreateFailureMessageFn = Callable[[Exception], str]
FetchFailureMessageFn = Callable[[Exception], str]
ResultMissingMessageFn = Callable[[], str]
TaskMissingMessageFn = Callable[[], str]
ConfigMissingMessageFn = Callable[[], str]


@dataclass(slots=True)
class GenerationRunnerConfig:
    media_type: str
    provider_media: str
    logger_name: str
    client_timeout: int
    max_wait_seconds: int
    poll_interval_seconds: int
    initial_status_ttl: int = 7200
    done_status_ttl: int = 86400
    progress_ttl: int = 7200
    set_progress: SetProgressFn | None = None
    update_task: UpdateTaskFn | None = None
    fetch_user_id: FetchUserIdFn | None = None
    mark_failed: MarkTerminalFn | None = None
    mark_timeout: MarkTerminalFn | None = None
    build_payload: PayloadBuilderFn | None = None
    materialize_result: MaterializeFn | None = None
    is_download_error: IsDownloadErrorFn | None = None
    validate_inputs: Callable[[], str | None] | None = None
    config_missing_message: ConfigMissingMessageFn | None = None
    task_missing_message: TaskMissingMessageFn | None = None
    create_failure_message: CreateFailureMessageFn | None = None
    create_parse_failure_message: CreateFailureMessageFn | None = None
    poll_failure_log_message: str = "轮询 ToAPIS 异常: %s"
    poll_parse_log_message: str = "ToAPIS 轮询响应解析失败: %s"
    missing_provider_task_message: str = "ToAPIS 未返回 task id"
    result_missing_message: ResultMissingMessageFn | None = None
    provider_failed_message: str = "ToAPIS 任务失败"
    wait_timeout_message: str = "等待 ToAPIS 任务超时"
    request_timeout_message: str = "请求 ToAPIS 超时"
    unexpected_failure_log_message: str = "任务失败详细错误: %s"
    download_failure_message: CreateFailureMessageFn | None = None
    upload_failure_message: CreateFailureMessageFn | None = None
    transport_factory: Callable[[], httpx.AsyncBaseTransport] | None = None
    client_factory: Callable[..., Any] | None = None
    create_generation_fn: Callable[..., Awaitable[dict]] = create_generation
    fetch_generation_fn: Callable[..., Awaitable[dict]] = fetch_generation
    extract_provider_task_id_fn: Callable[[dict], str | None] = extract_provider_task_id
    extract_provider_status_fn: Callable[[dict], str | None] = extract_provider_status
    extract_provider_progress_fn: Callable[[dict], int | None] = extract_provider_progress
    extract_provider_error_fn: Callable[[dict], str | None] = extract_provider_error
    extract_result_url_fn: Callable[[dict], str | None] = extract_result_url
    sleep_fn: Callable[[float], Awaitable[None]] = asyncio.sleep
    monotonic_fn: Callable[[], float] = time.monotonic


def _media_log_extra(media_type: str, task_id: str, provider_task_id: str | None = None) -> dict[str, Any]:
    extra = {"task_id": task_id, "media_type": media_type}
    if provider_task_id:
        extra["provider_task_id"] = provider_task_id
    return extra


async def _mark_processing(
    redis,
    task_id: str,
    config: GenerationRunnerConfig,
) -> None:
    await set_task_status(
        redis,
        config.media_type,
        task_id,
        "processing",
        ttl=config.initial_status_ttl,
    )
    if config.set_progress is not None:
        await config.set_progress(redis, task_id, 0)
    if config.update_task is not None:
        await config.update_task(task_id, status="processing", progress=0)


async def _handle_progress(
    redis,
    task_id: str,
    provider_progress: int | None,
    config: GenerationRunnerConfig,
) -> None:
    if provider_progress is None:
        return
    if config.set_progress is not None:
        await config.set_progress(redis, task_id, provider_progress)
    if config.update_task is not None:
        await config.update_task(task_id, progress=provider_progress)


async def _finalize_success(
    redis,
    task_id: str,
    uploaded,
    config: GenerationRunnerConfig,
) -> None:
    if config.update_task is not None:
        await config.update_task(
            task_id,
            status="done",
            result_url=uploaded.url,
            progress=100,
        )
    await set_task_result(redis, config.media_type, task_id, uploaded.url)
    if config.set_progress is not None:
        await config.set_progress(redis, task_id, 100)
    await set_task_status(
        redis,
        config.media_type,
        task_id,
        "done",
        ttl=config.done_status_ttl,
    )


async def run_generation_task(
    ctx,
    task_id: str,
    *,
    config: GenerationRunnerConfig,
) -> None:
    redis = ctx["redis"]
    task_logger = logging.getLogger(config.logger_name)

    try:
        await _mark_processing(redis, task_id, config)

        if not TOAPIS_KEY:
          if config.mark_failed is not None and config.config_missing_message is not None:
              await config.mark_failed(redis, task_id, config.config_missing_message())
          return

        user_id = await config.fetch_user_id(task_id) if config.fetch_user_id is not None else None
        if not user_id:
            if config.mark_failed is not None and config.task_missing_message is not None:
                await config.mark_failed(redis, task_id, config.task_missing_message())
            return

        if config.validate_inputs is not None:
            validation_error = config.validate_inputs()
            if validation_error:
                if config.mark_failed is not None:
                    await config.mark_failed(redis, task_id, validation_error)
                return

        payload = config.build_payload() if config.build_payload is not None else {}
        transport = config.transport_factory() if config.transport_factory is not None else httpx.AsyncHTTPTransport(proxy=None)
        client_factory = config.client_factory or httpx.AsyncClient
        async with client_factory(timeout=config.client_timeout, transport=transport) as client:
            try:
                create_result = await config.create_generation_fn(
                    client,
                    media=config.provider_media,
                    payload=payload,
                )
            except httpx.HTTPError as exc:
                if config.mark_failed is not None and config.create_failure_message is not None:
                    await config.mark_failed(redis, task_id, config.create_failure_message(exc))
                return
            except ValueError as exc:
                if config.mark_failed is not None and config.create_parse_failure_message is not None:
                    await config.mark_failed(redis, task_id, config.create_parse_failure_message(exc))
                return

            task_logger.debug(
                "toapis 创建响应: %s",
                create_result,
                extra=_media_log_extra(config.media_type, task_id),
            )

            provider_task_id = config.extract_provider_task_id_fn(create_result)
            if not provider_task_id:
                err = config.extract_provider_error_fn(create_result) or config.missing_provider_task_message
                if config.mark_failed is not None:
                    await config.mark_failed(redis, task_id, err)
                return

            if config.update_task is not None:
                await config.update_task(task_id, provider_task_id=provider_task_id)

            deadline = config.monotonic_fn() + config.max_wait_seconds
            final_url: str | None = None
            final_error: str | None = None

            while config.monotonic_fn() < deadline:
                await config.sleep_fn(config.poll_interval_seconds)
                try:
                    poll_result = await config.fetch_generation_fn(
                        client,
                        media=config.provider_media,
                        provider_task_id=provider_task_id,
                    )
                except httpx.HTTPError as exc:
                    task_logger.warning(
                        config.poll_failure_log_message,
                        exc,
                        extra=_media_log_extra(config.media_type, task_id, provider_task_id),
                    )
                    continue
                except ValueError as exc:
                    task_logger.warning(
                        config.poll_parse_log_message,
                        exc,
                        extra=_media_log_extra(config.media_type, task_id, provider_task_id),
                    )
                    continue

                provider_status = config.extract_provider_status_fn(poll_result)
                provider_progress = config.extract_provider_progress_fn(poll_result)
                await _handle_progress(redis, task_id, provider_progress, config)

                if provider_status in TOAPIS_STATUS_DONE:
                    final_url = config.extract_result_url_fn(poll_result)
                    if not final_url:
                        final_error = config.result_missing_message() if config.result_missing_message is not None else "ToAPIS 已完成但未返回结果 URL"
                    break

                if provider_status in TOAPIS_STATUS_FAILED:
                    final_error = config.extract_provider_error_fn(poll_result) or config.provider_failed_message
                    break
            else:
                if config.mark_timeout is not None:
                    await config.mark_timeout(redis, task_id, config.wait_timeout_message)
                return

            if not final_url:
                if config.mark_failed is not None:
                    await config.mark_failed(redis, task_id, final_error or config.provider_failed_message)
                return

            try:
                uploaded = await config.materialize_result(
                    user_id=user_id,
                    url=final_url,
                    client=client,
                )
            except Exception as exc:
                if config.is_download_error is not None and config.is_download_error(exc):
                    if config.mark_failed is not None and config.download_failure_message is not None:
                        await config.mark_failed(redis, task_id, config.download_failure_message(exc))
                    return
                task_logger.exception(
                    config.upload_failure_message(exc) if config.upload_failure_message is not None else "OSS 上传失败",
                    extra=_media_log_extra(config.media_type, task_id),
                )
                if config.mark_failed is not None and config.upload_failure_message is not None:
                    await config.mark_failed(redis, task_id, config.upload_failure_message(exc))
                return

        await _finalize_success(redis, task_id, uploaded, config)

    except httpx.TimeoutException:
        if config.mark_timeout is not None:
            await config.mark_timeout(redis, task_id, config.request_timeout_message)
    except Exception as exc:
        task_logger.exception(
            config.unexpected_failure_log_message,
            exc,
            extra=_media_log_extra(config.media_type, task_id),
        )
        if config.mark_failed is not None:
            await config.mark_failed(redis, task_id, str(exc))
