import os

from arq.connections import RedisSettings
from dotenv import load_dotenv

from app.worker.tasks import generate_image, generate_video

load_dotenv()


class WorkerSettings:
    functions = [generate_image, generate_video]
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    job_timeout = int(os.getenv("ARQ_JOB_TIMEOUT", "3000"))
    max_jobs = int(os.getenv("ARQ_MAX_JOBS", "5"))
