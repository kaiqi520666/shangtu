import logging

from app.core.generated_media_storage import materialize_video_to_oss
from app.core.providers.toapis_provider import (
    VIDEO_MAX_WAIT_SECONDS,
    VIDEO_POLL_INTERVAL_SECONDS,
    build_video_create_payload,
    get_video_provider_label,
    is_video_provider_configured,
)
from app.core.task_state import set_task_progress
from app.worker.task_failures import (
    mark_video_failed,
    mark_video_timeout,
)
from app.worker.generation_runner import GenerationRunnerConfig, run_generation_task
from app.worker.task_state_sync import fetch_video_task_context, update_video_task_in_db

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
    video_urls: list[str] | None = None,
    audio_urls: list[str] | None = None,
    generate_audio: bool = False,
    enable_web_search: bool = False,
):
    provider_label = get_video_provider_label()

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
        return f"创建 {provider_label} 视频任务失败: {reason}"

    config = GenerationRunnerConfig(
        media_type="video",
        provider_media="video",
        logger_name="app.worker.video_tasks",
        client_timeout=90,
        max_wait_seconds=VIDEO_MAX_WAIT_SECONDS,
        poll_interval_seconds=VIDEO_POLL_INTERVAL_SECONDS,
        set_progress=_set_video_progress,
        update_task=update_video_task_in_db,
        fetch_task_context=fetch_video_task_context,
        mark_failed=mark_video_failed,
        mark_timeout=mark_video_timeout,
        build_payload=lambda: build_video_create_payload(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            image_urls=image_urls,
            input_video_url=input_video_url,
            video_urls=video_urls or [],
            audio_urls=audio_urls or [],
            generate_audio=generate_audio,
            enable_web_search=enable_web_search,
            client_business_id=task_id,
        ),
        materialize_result=materialize_video_to_oss,
        validate_inputs=None,
        provider_configured=is_video_provider_configured,
        config_missing_message=lambda: f"{provider_label} 视频服务 Key 未配置，无法调用视频生成服务",
        task_missing_message=lambda: "视频任务不存在或已删除",
        create_failure_message=create_failure_message,
        create_parse_failure_message=lambda exc: f"{provider_label} 视频创建响应解析失败: {exc}",
        poll_failure_log_message=f"轮询 {provider_label} 视频异常: %s",
        poll_parse_log_message=f"{provider_label} 视频轮询响应解析失败: %s",
        missing_provider_task_message=f"{provider_label} 未返回 video task id",
        result_missing_message=lambda: f"{provider_label} 已完成但未返回视频 URL",
        provider_failed_message=f"{provider_label} 视频任务失败",
        wait_timeout_message=f"等待 {provider_label} 视频任务超时",
        request_timeout_message=f"请求 {provider_label} 视频服务超时",
        unexpected_failure_log_message="视频任务失败详细错误: %s",
        download_failure_message=lambda exc: f"下载生成视频失败: {exc}",
        upload_failure_message=lambda exc: f"视频上传 OSS 失败: {exc}",
    )
    await run_generation_task(ctx, task_id, config=config)
