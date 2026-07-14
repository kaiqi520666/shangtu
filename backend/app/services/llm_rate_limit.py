import logging
from typing import Any

from app.core.rate_limit import increment_fixed_window


logger = logging.getLogger("app.services.llm_rate_limit")

LLM_RATE_LIMIT_MESSAGE = "操作过于频繁，请稍后再试"
LLM_RATE_LIMITS = {
    "image-analyze": (6, 60),
    "image-strategy": (5, 300),
    "video-strategy": (5, 300),
    "prompt-optimize": (15, 60),
}


async def allow_llm_request(redis: Any, user_id: int, capability: str) -> bool:
    limit, window_seconds = LLM_RATE_LIMITS[capability]
    try:
        count = await increment_fixed_window(
            redis,
            f"llm:{capability}:{user_id}",
            window_seconds,
        )
    except Exception:
        logger.warning(
            "LLM rate limit unavailable; allowing request capability=%s user_id=%s",
            capability,
            user_id,
            exc_info=True,
        )
        return True
    return count <= limit
