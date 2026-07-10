import os

from arq.connections import RedisSettings
from dotenv import load_dotenv

from app.worker.tasks import generate_image, generate_video
from app.worker.heygen_tasks import submit_digital_human_task, submit_video_translation_task
from app.worker.voiceover_tasks import generate_voiceover
from app.core.logging_config import configure_logging

load_dotenv()
configure_logging()


class WorkerSettings:
    functions = [
        generate_image,
        generate_video,
        submit_digital_human_task,
        submit_video_translation_task,
        generate_voiceover,
    ]
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    job_timeout = int(os.getenv("ARQ_JOB_TIMEOUT", "3000"))
    max_jobs = int(os.getenv("ARQ_MAX_JOBS", "5"))
