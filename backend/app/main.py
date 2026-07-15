from contextlib import asynccontextmanager
import logging

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.core.database import SessionLocal
from app.core.config import get_env, validate_runtime_config
from app.core.logging_config import configure_logging
from app.core.system_settings import seed_default_billing_settings
from app.routers import account, admin, asset, auth, billing, digital_human, distribution, generation, image_generation, outfit, video, video_translation, voiceover
from app.schemas.response import fail

configure_logging()

logger = logging.getLogger("app.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_config()
    async with SessionLocal() as db:
        await seed_default_billing_settings(db)
        await db.commit()

    app.state.redis_pool = await create_pool(
        RedisSettings.from_dsn(get_env("REDIS_URL", "redis://localhost:6379"))
    )
    yield

    await app.state.redis_pool.close()


app = FastAPI(title="ShangTu API", lifespan=lifespan)


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content=fail("系统异常，请稍后重试").model_dump(),
    )

app.include_router(admin.router)
app.include_router(account.router)
app.include_router(distribution.router)
app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(image_generation.router)
app.include_router(generation.router)
app.include_router(digital_human.router)
app.include_router(asset.router)
app.include_router(outfit.router)
app.include_router(video.router)
app.include_router(video_translation.router)
app.include_router(voiceover.router)
