import hashlib
from typing import Any


def hashed_identifier(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


async def increment_fixed_window(redis: Any, key: str, window_seconds: int) -> int:
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_seconds)
    return count


async def read_counter(redis: Any, key: str) -> int:
    value = await redis.get(key)
    if value is None:
        return 0
    if isinstance(value, bytes):
        value = value.decode()
    return int(value)
