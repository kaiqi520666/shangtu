import asyncio
import json
import logging
from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse


def _encode_event(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


def text_streaming_response(
    source: AsyncIterator[str],
    *,
    logger: logging.Logger,
    error_log: str,
    error_message: str,
) -> StreamingResponse:
    async def events():
        try:
            async for content in source:
                yield _encode_event("delta", {"content": content})
            yield _encode_event("done", {})
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(error_log)
            yield _encode_event("error", {"message": error_message})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
