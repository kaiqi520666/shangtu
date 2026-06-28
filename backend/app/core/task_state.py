import json
from dataclasses import dataclass
from typing import Any, Iterable


MEDIA_KEY_PREFIX = {
    "image": "task",
    "video": "video_task",
}

TASK_STATE_FIELDS = ("status", "result", "error", "progress")
PENDING_STATUSES = ("pending", "processing")


@dataclass
class MergedTaskState:
    status: str
    result_url: str | None
    error_message: str | None
    progress: int


def task_state_key(media_type: str, task_id: str, field: str) -> str:
    prefix = MEDIA_KEY_PREFIX[media_type]
    if field not in TASK_STATE_FIELDS:
        raise ValueError(f"Unsupported task state field: {field}")
    return f"{prefix}:{task_id}:{field}"


def task_state_keys(
    media_type: str,
    task_id: str,
    fields: Iterable[str] = TASK_STATE_FIELDS,
) -> list[str]:
    return [task_state_key(media_type, task_id, field) for field in fields]


def redis_str(value: Any) -> str | None:
    if value is None:
        return None
    return value.decode() if isinstance(value, bytes) else str(value)


def parse_redis_result_url(value: Any) -> str | None:
    raw = redis_str(value)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    url = parsed.get("url")
    return url if isinstance(url, str) and url else None


def clamp_progress(value: int) -> int:
    return max(0, min(100, int(value)))


async def read_redis_task_state(redis_pool, media_type: str, task_id: str) -> tuple[Any, Any, Any, Any]:
    async with redis_pool.pipeline() as pipe:
        pipe.get(task_state_key(media_type, task_id, "status"))
        pipe.get(task_state_key(media_type, task_id, "error"))
        pipe.get(task_state_key(media_type, task_id, "progress"))
        pipe.get(task_state_key(media_type, task_id, "result"))
        return await pipe.execute()


async def merge_task_state(
    redis_pool,
    media_type: str,
    task_id: str,
    *,
    db_status: str,
    db_result_url: str | None,
    db_error_message: str | None,
    db_progress: int | None,
) -> MergedTaskState:
    status = db_status
    result_url = db_result_url
    error_message = db_error_message
    progress = db_progress or 0

    if redis_pool is not None:
        try:
            live_status, live_error, live_progress, live_result = await read_redis_task_state(
                redis_pool,
                media_type,
                task_id,
            )

            live_status_str: str | None = None
            if live_status:
                live_status_str = redis_str(live_status)
                # 防止 Redis 残留的旧 done 覆盖 DB 的 pending/processing
                if db_status in PENDING_STATUSES:
                    if live_status_str != "done":
                        status = live_status_str
                else:
                    status = live_status_str

            if live_error:
                error_message = redis_str(live_error)
            if live_progress:
                try:
                    progress = clamp_progress(int(redis_str(live_progress)))
                except (TypeError, ValueError):
                    pass

            # 读取 Redis result，无论 DB result_url 是否有值都要尝试。
            redis_result_url = parse_redis_result_url(live_result)
            if redis_result_url:
                result_url = redis_result_url

            if live_status_str == "done" and db_status in PENDING_STATUSES:
                status = "done" if redis_result_url else "processing"
        except Exception:
            pass

    # Redis 已写入 status=done 但 DB/result 还没更新时，降级为 processing 继续轮询。
    if status == "done" and not result_url:
        status = "processing"

    if status == "done":
        progress = 100

    return MergedTaskState(
        status=status,
        result_url=result_url,
        error_message=error_message,
        progress=progress,
    )


async def set_task_status(
    redis,
    media_type: str,
    task_id: str,
    status: str,
    *,
    ttl: int,
) -> None:
    await redis.set(task_state_key(media_type, task_id, "status"), status, ex=ttl)


async def set_task_progress(
    redis,
    media_type: str,
    task_id: str,
    value: int,
    *,
    ttl: int = 7200,
) -> None:
    await redis.set(
        task_state_key(media_type, task_id, "progress"),
        str(clamp_progress(value)),
        ex=ttl,
    )


async def set_task_error(
    redis,
    media_type: str,
    task_id: str,
    message: str,
    *,
    ttl: int = 3600,
) -> None:
    await redis.set(task_state_key(media_type, task_id, "error"), message, ex=ttl)


async def set_task_result(
    redis,
    media_type: str,
    task_id: str,
    result_url: str,
    *,
    ttl: int = 86400,
) -> None:
    await redis.set(
        task_state_key(media_type, task_id, "result"),
        json.dumps({"url": result_url}),
        ex=ttl,
    )


async def clear_task_state_fields(
    redis,
    media_type: str,
    task_id: str,
    fields: Iterable[str],
) -> None:
    keys = task_state_keys(media_type, task_id, fields)
    if keys:
        await redis.delete(*keys)
