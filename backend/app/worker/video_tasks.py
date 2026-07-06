import logging

from app.core.generated_media_storage import materialize_video_to_oss
from app.core.providers.toapis_provider import (
    VIDEO_MAX_WAIT_SECONDS,
    VIDEO_POLL_INTERVAL_SECONDS,
    build_video_create_payload,
)
from app.core.task_state import set_task_progress
from app.worker.task_failures import (
    mark_video_failed,
    mark_video_timeout,
)
from app.worker.generation_runner import GenerationRunnerConfig, run_generation_task
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
    image_urls: list[str],
    input_video_url: str = "",
):
    def create_failure_message(exc):
        detail = ""
        resp = getattr(exc, "response", None)
        if resp is not None:
            try:
                detail = (resp.text or "")[:500]
            except Exception:
                detail = ""
            reason = f"{exc} | {detail}" if detail else str(exc)
        else:
            reason = f"{type(exc).__name__}: {exc!r}"
        return f"创建 ToAPIS 视频任务失败: {reason}"

    config = GenerationRunnerConfig(
        media_type="video",
        provider_media="video",
        logger_name="app.worker.video_tasks",
        client_timeout=90,
        max_wait_seconds=VIDEO_MAX_WAIT_SECONDS,
        poll_interval_seconds=VIDEO_POLL_INTERVAL_SECONDS,
        set_progress=_set_video_progress,
        update_task=update_video_task_in_db,
        fetch_user_id=fetch_video_task_user_id,
        mark_failed=mark_video_failed,
        mark_timeout=mark_video_timeout,
        build_payload=lambda: build_video_create_payload(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            image_urls=image_urls,
            input_video_url=input_video_url,
            client_business_id=task_id,
        ),
        materialize_result=materialize_video_to_oss,
        validate_inputs=None,
        config_missing_message=lambda: "TOAPIS_KEY 未配置，无法调用视频生成服务",
        task_missing_message=lambda: "视频任务不存在或已删除",
        create_failure_message=create_failure_message,
        create_parse_failure_message=lambda exc: f"ToAPIS 视频创建响应解析失败: {exc}",
        poll_failure_log_message="轮询 ToAPIS 视频异常: %s",
        poll_parse_log_message="ToAPIS 视频轮询响应解析失败: %s",
        missing_provider_task_message="ToAPIS 未返回 video task id",
        result_missing_message=lambda: "ToAPIS 已完成但未返回视频 URL",
        provider_failed_message="ToAPIS 视频任务失败",
        wait_timeout_message="等待 ToAPIS 视频任务超时",
        request_timeout_message="请求 ToAPIS 视频服务超时",
        unexpected_failure_log_message="视频任务失败详细错误: %s",
        download_failure_message=lambda exc: f"下载生成视频失败: {exc}",
        upload_failure_message=lambda exc: f"视频上传 OSS 失败: {exc}",
    )
    await run_generation_task(ctx, task_id, config=config)
