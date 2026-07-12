import os
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv()


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def require_env(name: str) -> str:
    value = get_env(name)
    if not value:
        raise RuntimeError(f"{name} 未配置")
    return value


def get_int_env(name: str, default: int) -> int:
    value = get_env(name)
    return int(value) if value is not None else default


def validate_runtime_config() -> None:
    database_url = get_env(
        "DATABASE_URL",
        "postgresql+asyncpg://admin:123456@localhost/shangtu",
    )
    if not database_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError("DATABASE_URL 必须使用 postgresql+asyncpg")
    redis_url = get_env("REDIS_URL", "redis://localhost:6379")
    if urlsplit(redis_url).scheme not in {"redis", "rediss"}:
        raise RuntimeError("REDIS_URL 格式不正确")
    require_env("SECRET_KEY")
    provider = get_env("VIDEO_PROVIDER", "topenrouter").lower()
    if provider not in {"toapis", "topenrouter"}:
        raise RuntimeError("VIDEO_PROVIDER 仅支持 toapis 或 topenrouter")
    if provider == "toapis":
        require_env("TOAPIS_KEY")
    elif not (get_env("TOPENROUTER_KEY") or get_env("TOPENROUTER_API_KEY")):
        raise RuntimeError("TOPENROUTER_KEY 未配置")
