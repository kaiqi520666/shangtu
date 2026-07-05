import asyncio
import os
import uuid
from dataclasses import dataclass
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

import oss2
from dotenv import load_dotenv

from app.core.time import utc_now

load_dotenv()

MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 300 * 1024 * 1024
MAX_AUDIO_SIZE = 20 * 1024 * 1024
IMAGE_URL_VARIANTS = {
    "thumb_url": "image/resize,w_480/quality,q_80/format,webp",
    "preview_url": "image/resize,w_1200/quality,q_85/format,webp",
}
PROCESSABLE_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/webm": "webm",
    "video/x-matroska": "mkv",
}
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/wave": "wav",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/aac": "aac",
    "audio/ogg": "ogg",
    "audio/webm": "webm",
    "audio/flac": "flac",
    "audio/x-flac": "flac",
}


@dataclass(frozen=True)
class UploadedImage:
    url: str
    object_key: str
    content_type: str
    size: int


@dataclass(frozen=True)
class UploadedFile:
    url: str
    object_key: str
    content_type: str
    size: int


class OssConfigError(RuntimeError):
    pass


def get_oss_config() -> dict[str, str]:
    config = {
        "access_key_id": os.getenv("OSS_ACCESS_KEY_ID"),
        "access_key_secret": os.getenv("OSS_ACCESS_KEY_SECRET"),
        "endpoint": os.getenv("OSS_ENDPOINT"),
        "bucket_name": os.getenv("OSS_BUCKET_NAME"),
        "public_base_url": os.getenv("OSS_PUBLIC_BASE_URL"),
    }
    missing = [key for key, value in config.items() if key != "public_base_url" and not value]
    if missing:
        raise OssConfigError(f"OSS配置缺失: {', '.join(missing)}")
    return config


def build_image_object_key(user_id: int, content_type: str, source: str = "uploads") -> str:
    extension = ALLOWED_IMAGE_TYPES[content_type]
    now = utc_now()
    if source.startswith("system/"):
        return f"{source}/{now:%Y/%m}/{uuid.uuid4().hex}.{extension}"
    return f"{source}/{user_id}/{now:%Y/%m}/{uuid.uuid4().hex}.{extension}"


def build_file_object_key(
    user_id: int,
    extension: str,
    source: str = "uploads",
) -> str:
    now = utc_now()
    if source.startswith("system/"):
        return f"{source}/{now:%Y/%m}/{uuid.uuid4().hex}.{extension}"
    return f"{source}/{user_id}/{now:%Y/%m}/{uuid.uuid4().hex}.{extension}"


def build_public_url(object_key: str, config: dict[str, str]) -> str:
    public_base_url = config.get("public_base_url")
    if public_base_url:
        return f"{public_base_url.rstrip('/')}/{object_key}"

    endpoint = config["endpoint"].replace("https://", "").replace("http://", "").rstrip("/")
    return f"https://{config['bucket_name']}.{endpoint}/{object_key}"


def image_url_variants(url: str | None) -> dict[str, str]:
    clean_url = str(url or "").strip()
    if not clean_url:
        return {"result_url": "", "thumb_url": "", "preview_url": ""}

    parsed = urlsplit(clean_url)
    public_base_url = (os.getenv("OSS_PUBLIC_BASE_URL") or "").rstrip("/")
    public_host = urlsplit(public_base_url).netloc if public_base_url else ""
    endpoint_host = (os.getenv("OSS_ENDPOINT") or "").replace("https://", "").replace("http://", "").rstrip("/")
    bucket_host = f"{os.getenv('OSS_BUCKET_NAME')}.{endpoint_host}" if endpoint_host else ""
    if public_base_url and bucket_host and parsed.netloc == bucket_host:
        public_url = f"{public_base_url}/{parsed.path.lstrip('/')}"
        parsed = urlsplit(f"{public_url}?{parsed.query}" if parsed.query else public_url)
    else:
        public_url = clean_url

    supported_hosts = {host for host in (public_host, bucket_host) if host}
    can_process = (
        parsed.scheme in {"http", "https"}
        and parsed.path.lower().endswith(PROCESSABLE_IMAGE_EXTENSIONS)
        and parsed.netloc in supported_hosts
    )
    if not can_process:
        return {"result_url": public_url, "thumb_url": public_url, "preview_url": public_url}

    base_query = urlencode(
        [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key != "x-oss-process"]
    )
    base_url = urlunsplit(parsed._replace(query=""))
    variants = {"result_url": public_url}
    for key, process in IMAGE_URL_VARIANTS.items():
        process_query = f"x-oss-process={quote(process, safe='/,')}"
        query = "&".join(part for part in (base_query, process_query) if part)
        variants[key] = f"{base_url}?{query}"
    return variants


def upload_image_bytes_sync(
    *,
    user_id: int,
    content: bytes,
    content_type: str,
    source: str = "uploads",
) -> UploadedImage:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("图片格式不支持")

    if not content:
        raise ValueError("图片不能为空")

    if len(content) > MAX_IMAGE_SIZE:
        raise ValueError("图片不能超过10MB")

    config = get_oss_config()
    object_key = build_image_object_key(user_id, content_type, source)
    auth = oss2.Auth(config["access_key_id"], config["access_key_secret"])
    bucket = oss2.Bucket(auth, config["endpoint"], config["bucket_name"])
    bucket.put_object(object_key, content, headers={"Content-Type": content_type})

    return UploadedImage(
        url=build_public_url(object_key, config),
        object_key=object_key,
        content_type=content_type,
        size=len(content),
    )


async def upload_image_bytes(
    *,
    user_id: int,
    content: bytes,
    content_type: str,
    source: str = "uploads",
) -> UploadedImage:
    return await asyncio.to_thread(
        upload_image_bytes_sync,
        user_id=user_id,
        content=content,
        content_type=content_type,
        source=source,
    )


def upload_video_bytes_sync(
    *,
    user_id: int,
    content: bytes,
    content_type: str,
    source: str = "generated-videos",
) -> UploadedFile:
    if content_type not in ALLOWED_VIDEO_TYPES:
        raise ValueError("视频格式不支持")

    if not content:
        raise ValueError("视频不能为空")

    if len(content) > MAX_VIDEO_SIZE:
        raise ValueError("视频不能超过300MB")

    config = get_oss_config()
    object_key = build_file_object_key(
        user_id=user_id,
        extension=ALLOWED_VIDEO_TYPES[content_type],
        source=source,
    )
    auth = oss2.Auth(config["access_key_id"], config["access_key_secret"])
    bucket = oss2.Bucket(auth, config["endpoint"], config["bucket_name"])
    bucket.put_object(object_key, content, headers={"Content-Type": content_type})

    return UploadedFile(
        url=build_public_url(object_key, config),
        object_key=object_key,
        content_type=content_type,
        size=len(content),
    )


async def upload_video_bytes(
    *,
    user_id: int,
    content: bytes,
    content_type: str,
    source: str = "generated-videos",
) -> UploadedFile:
    return await asyncio.to_thread(
        upload_video_bytes_sync,
        user_id=user_id,
        content=content,
        content_type=content_type,
        source=source,
    )


def upload_audio_bytes_sync(
    *,
    user_id: int,
    content: bytes,
    content_type: str,
    source: str = "audio-uploads",
) -> UploadedFile:
    if content_type not in ALLOWED_AUDIO_TYPES:
        raise ValueError("音频格式不支持")

    if not content:
        raise ValueError("音频不能为空")

    if len(content) > MAX_AUDIO_SIZE:
        raise ValueError("音频不能超过20MB")

    config = get_oss_config()
    object_key = build_file_object_key(
        user_id=user_id,
        extension=ALLOWED_AUDIO_TYPES[content_type],
        source=source,
    )
    auth = oss2.Auth(config["access_key_id"], config["access_key_secret"])
    bucket = oss2.Bucket(auth, config["endpoint"], config["bucket_name"])
    bucket.put_object(object_key, content, headers={"Content-Type": content_type})

    return UploadedFile(
        url=build_public_url(object_key, config),
        object_key=object_key,
        content_type=content_type,
        size=len(content),
    )


async def upload_audio_bytes(
    *,
    user_id: int,
    content: bytes,
    content_type: str,
    source: str = "audio-uploads",
) -> UploadedFile:
    return await asyncio.to_thread(
        upload_audio_bytes_sync,
        user_id=user_id,
        content=content,
        content_type=content_type,
        source=source,
    )
