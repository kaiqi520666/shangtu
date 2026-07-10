from pathlib import PurePosixPath
from urllib.parse import urlparse

import httpx
from fastapi.responses import StreamingResponse

MEDIA_TYPES = {
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".png": "image/png",
    ".wav": "audio/wav",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
}


def remote_media_download_response(
    url: str,
    *,
    filename_stem: str,
    fallback_extension: str,
    media_type_override: str | None = None,
    timeout_seconds: int = 60,
) -> StreamingResponse:
    suffix = PurePosixPath(urlparse(url).path).suffix.lower()
    extension = suffix.lstrip(".") if suffix in MEDIA_TYPES else fallback_extension
    media_type = media_type_override or MEDIA_TYPES.get(f".{extension}", "application/octet-stream")

    async def stream():
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    yield chunk

    return StreamingResponse(
        stream(),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename_stem}.{extension}"'},
    )
