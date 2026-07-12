import logging

from app.core.generated_media_storage import materialize_to_oss
from app.core.providers.toapis_provider import (
    MAX_WAIT_SECONDS,
    POLL_INTERVAL_SECONDS,
    build_create_payload,
    validate_size,
)
from app.core.task_state import set_task_progress
from app.worker.task_failures import mark_failed, mark_timeout
from app.worker.generation_runner import GenerationRunnerConfig, run_generation_task
from app.worker.task_state_sync import fetch_image_task_context, update_task_in_db

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
    def create_failure_message(exc):
        resp = getattr(exc, "response", None)
        if resp is None:
            return f"创建 ToAPIS 任务失败: {type(exc).__name__}: {exc!r}"
        try:
            detail = (resp.text or "")[:500]
        except Exception:
            detail = ""
        reason = f"{exc} | {detail}" if detail else str(exc)
        return f"创建 ToAPIS 任务失败: {reason}"

    config = GenerationRunnerConfig(
        media_type="image",
        provider_media="image",
        logger_name="app.worker.image_tasks",
        client_timeout=60,
        max_wait_seconds=MAX_WAIT_SECONDS,
        poll_interval_seconds=POLL_INTERVAL_SECONDS,
        set_progress=_set_progress,
        update_task=update_task_in_db,
        fetch_task_context=fetch_image_task_context,
        mark_failed=mark_failed,
        mark_timeout=mark_timeout,
        build_payload=lambda: build_create_payload(
            prompt=prompt,
            ratio=ratio,
            resolution=resolution,
            image_urls=image_urls,
        ),
        materialize_result=materialize_to_oss,
        validate_inputs=lambda: validate_size(ratio, resolution),
        config_missing_message=lambda: "TOAPIS_KEY 未配置，无法调用生图服务",
        task_missing_message=lambda: "任务不存在或已删除",
        create_failure_message=create_failure_message,
        create_parse_failure_message=lambda exc: f"ToAPIS 创建响应解析失败: {exc}",
        result_missing_message=lambda: "ToAPIS 已完成但未返回结果图 URL",
        provider_failed_message="ToAPIS 任务失败",
        wait_timeout_message="等待 ToAPIS 任务超时",
        request_timeout_message="请求 ToAPIS 超时",
        unexpected_failure_log_message="任务失败详细错误: %s",
        download_failure_message=lambda exc: f"下载生成图失败: {exc}",
        upload_failure_message=lambda exc: f"OSS 上传失败: {exc}",
    )
    await run_generation_task(ctx, task_id, config=config)
