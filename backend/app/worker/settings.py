from arq.connections import RedisSettings

from app.worker.tasks import generate_image, generate_video
from app.worker.heygen_tasks import submit_digital_human_task, submit_video_translation_task
from app.worker.voiceover_tasks import generate_voiceover
from app.core.logging_config import configure_logging
from app.core.config import get_env, get_int_env, validate_runtime_config

validate_runtime_config()
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
        get_env("REDIS_URL", "redis://localhost:6379")
    )
    job_timeout = get_int_env("ARQ_JOB_TIMEOUT", 3000)
    max_jobs = get_int_env("ARQ_MAX_JOBS", 5)
