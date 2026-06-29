DEFAULT_IMAGE_CREDIT_COSTS: dict[str, int] = {
    "1K": 9,
    "2K": 12,
    "4K": 15,
}

DEFAULT_VIDEO_CREDIT_COSTS: dict[str, int] = {
    "720p": 36,
    "1080p": 64,
}


def normalize_image_resolution(resolution: str | None) -> str:
    return "".join(str(resolution or "").split()).upper()


def normalize_video_resolution(resolution: str | None) -> str:
    cleaned = "".join(str(resolution or "").split()).lower()
    if cleaned in {"480", "720", "1080"}:
        return f"{cleaned}p"
    return cleaned
