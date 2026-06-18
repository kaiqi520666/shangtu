from contextlib import asynccontextmanager
import os

from arq import create_pool
from arq.connections import RedisSettings
from dotenv import load_dotenv
from fastapi import FastAPI

from app.core.database import Base, engine
from app.core.schema_migrations import ensure_runtime_schema
from app.routers import admin, asset, auth, billing, generation, image, outfit, video
import app.models

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_runtime_schema(engine)

    app.state.redis_pool = await create_pool(
        RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
    )
    yield

    await app.state.redis_pool.close()


app = FastAPI(title="ShangTu API", lifespan=lifespan)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(image.router)
app.include_router(generation.router)
app.include_router(asset.router)
app.include_router(outfit.router)
app.include_router(video.router)
