DEFAULT_IMAGE_CREDIT_COSTS: dict[str, int] = {
    "1K": 1,
    "2K": 2,
    "4K": 4,
}

DEFAULT_VIDEO_CREDIT_COSTS: dict[str, int] = {
    "480p": 1,
    "720p": 2,
    "1080p": 4,
}


def normalize_image_resolution(resolution: str | None) -> str:
    return "".join(str(resolution or "").split()).upper()


def normalize_video_resolution(resolution: str | None) -> str:
    cleaned = "".join(str(resolution or "").split()).lower()
    if cleaned in {"480", "720", "1080"}:
        return f"{cleaned}p"
    return cleaned
