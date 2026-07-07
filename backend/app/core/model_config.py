import os

from dotenv import load_dotenv

load_dotenv()


def _env_model(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def _video_model_default() -> str:
    provider = (os.getenv("VIDEO_PROVIDER") or "topenrouter").strip().lower()
    return "seedance-2" if provider == "toapis" else "doubao-seedance-2.0"


QWEN_TEXT_MODEL = _env_model("QWEN_TEXT_MODEL", "qwen3.6-flash")
IMAGE_GENERATE_MODEL = _env_model("IMAGE_GENERATE_MODEL", "gpt-image-2")
VIDEO_GENERATE_MODEL = _env_model("VIDEO_GENERATE_MODEL", _video_model_default())
