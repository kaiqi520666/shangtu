import os

from dotenv import load_dotenv

load_dotenv()

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


def get_image_credit_cost(resolution: str | None) -> int:
    normalized = normalize_image_resolution(resolution)
    if normalized not in DEFAULT_IMAGE_CREDIT_COSTS:
        supported = " / ".join(DEFAULT_IMAGE_CREDIT_COSTS.keys())
        raise ValueError(f"不支持的清晰度：{resolution}，请选择 {supported}")

    env_key = f"IMAGE_CREDIT_COST_{normalized}"
    raw_value = os.getenv(env_key)
    if raw_value is None or raw_value.strip() == "":
        return DEFAULT_IMAGE_CREDIT_COSTS[normalized]

    try:
        cost = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{env_key} 必须是正整数") from exc

    if cost < 1:
        raise ValueError(f"{env_key} 必须大于等于 1")
    return cost


def get_image_credit_costs() -> dict[str, int]:
    return {
        resolution: get_image_credit_cost(resolution)
        for resolution in DEFAULT_IMAGE_CREDIT_COSTS
    }


def normalize_video_resolution(resolution: str | None) -> str:
    cleaned = "".join(str(resolution or "").split()).lower()
    if cleaned in {"480", "720", "1080"}:
        return f"{cleaned}p"
    return cleaned


def get_video_credit_cost_per_second(resolution: str | None) -> int:
    normalized = normalize_video_resolution(resolution)
    if normalized not in DEFAULT_VIDEO_CREDIT_COSTS:
        supported = " / ".join(DEFAULT_VIDEO_CREDIT_COSTS.keys())
        raise ValueError(f"不支持的视频清晰度：{resolution}，请选择 {supported}")

    env_key = f"VIDEO_CREDIT_COST_{normalized.upper()}"
    raw_value = os.getenv(env_key)
    if raw_value is None or raw_value.strip() == "":
        return DEFAULT_VIDEO_CREDIT_COSTS[normalized]

    try:
        cost = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{env_key} 必须是正整数") from exc

    if cost < 1:
        raise ValueError(f"{env_key} 必须大于等于 1")
    return cost


def get_video_credit_costs() -> dict[str, int]:
    return {
        resolution: get_video_credit_cost_per_second(resolution)
        for resolution in DEFAULT_VIDEO_CREDIT_COSTS
    }
