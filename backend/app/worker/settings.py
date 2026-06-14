import os

from arq.connections import RedisSettings
from dotenv import load_dotenv

from app.worker.tasks import generate_image

load_dotenv()


class WorkerSettings:
    functions = [generate_image]
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    job_timeout = 1500
    max_jobs = int(os.getenv("ARQ_MAX_JOBS", "5"))
