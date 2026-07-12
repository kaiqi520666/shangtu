from app.core.config import get_env


def _env_model(name: str, default: str) -> str:
    return get_env(name, default)


def _video_model_default() -> str:
    provider = get_env("VIDEO_PROVIDER", "topenrouter").lower()
    return "seedance-2" if provider == "toapis" else "doubao-seedance-2.0"


QWEN_TEXT_MODEL = _env_model("QWEN_TEXT_MODEL", "qwen3.6-flash")
IMAGE_GENERATE_MODEL = _env_model("IMAGE_GENERATE_MODEL", "gpt-image-2")
VIDEO_GENERATE_MODEL = _env_model("VIDEO_GENERATE_MODEL", _video_model_default())
