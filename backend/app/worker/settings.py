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
    job_timeout = 330
    max_jobs = 5