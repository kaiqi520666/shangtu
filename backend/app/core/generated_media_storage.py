import httpx

from app.core.oss import ALLOWED_IMAGE_TYPES, ALLOWED_VIDEO_TYPES, upload_image_bytes, upload_video_bytes

DEFAULT_GENERATED_CONTENT_TYPE = "image/png"
DEFAULT_GENERATED_VIDEO_CONTENT_TYPE = "video/mp4"


def normalize_content_type(raw: str | None) -> str:
    if not raw:
        return DEFAULT_GENERATED_CONTENT_TYPE
    main = raw.split(";", 1)[0].strip().lower()
    if main == "image/jpg":
        main = "image/jpeg"
    if main in ALLOWED_IMAGE_TYPES:
        return main
    return DEFAULT_GENERATED_CONTENT_TYPE


def normalize_video_content_type(raw: str | None, url: str | None = None) -> str:
    if raw:
        main = raw.split(";", 1)[0].strip().lower()
        if main in ALLOWED_VIDEO_TYPES:
            return main
    url_lower = (url or "").lower()
    if url_lower.endswith(".webm"):
        return "video/webm"
    if url_lower.endswith(".mov"):
        return "video/quicktime"
    if url_lower.endswith(".mkv"):
        return "video/x-matroska"
    return DEFAULT_GENERATED_VIDEO_CONTENT_TYPE


async def materialize_to_oss(
    *,
    user_id: int,
    url: str,
    client: httpx.AsyncClient,
):
    download = await client.get(url)
    download.raise_for_status()
    content_bytes = download.content
    content_type = normalize_content_type(download.headers.get("content-type"))

    return await upload_image_bytes(
        user_id=user_id,
        content=content_bytes,
        content_type=content_type,
        source="generated",
    )


async def materialize_video_to_oss(
    *,
    user_id: int,
    url: str,
    client: httpx.AsyncClient,
):
    download = await client.get(url)
    download.raise_for_status()
    content_bytes = download.content
    content_type = normalize_video_content_type(
        download.headers.get("content-type"),
        url,
    )

    return await upload_video_bytes(
        user_id=user_id,
        content=content_bytes,
        content_type=content_type,
        source="generated-videos",
    )
