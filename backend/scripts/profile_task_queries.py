import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import Base, DATABASE_URL  # noqa: E402
import app.models  # noqa: E402,F401

DATABASE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+_perf$")
INDEXES = {
    "ix_generation_jobs_user_scenario_active_created": (
        "generation_jobs (user_id, scenario, archived, created_at DESC)"
    ),
    "ix_image_tasks_user_active_created": (
        "image_tasks (user_id, archived, created_at DESC)"
    ),
    "ix_image_tasks_job_active_current": (
        "image_tasks (job_id, user_id, archived, replaced_by_task_id)"
    ),
    "ix_image_tasks_status_created": "image_tasks (status, created_at DESC)",
    "ix_video_tasks_user_active_status_scenario_created": (
        "video_tasks (user_id, archived, status, scenario, created_at DESC)"
    ),
    "ix_video_tasks_job_user_active_scenario": (
        "video_tasks (job_id, user_id, archived, scenario)"
    ),
    "ix_video_tasks_status_created": "video_tasks (status, created_at DESC)",
}

QUERIES = {
    "user_job_history": """
        SELECT id, status, created_at
        FROM generation_jobs
        WHERE user_id = 1 AND scenario = 'product_image' AND archived = false
        ORDER BY created_at DESC
    """,
    "user_image_job_tasks": """
        SELECT job_id, status, created_at
        FROM image_tasks
        WHERE user_id = 1 AND job_id = '00000000000000000000000000000001'
          AND archived = false AND replaced_by_task_id IS NULL
    """,
    "user_image_assets": """
        SELECT id, result_url, created_at
        FROM image_tasks
        WHERE user_id = 1 AND status = 'done' AND archived = false
        ORDER BY created_at DESC LIMIT 20
    """,
    "user_video_assets": """
        SELECT id, result_url, created_at
        FROM video_tasks
        WHERE user_id = 1 AND status = 'done' AND archived = false
          AND scenario = 'digital_human'
        ORDER BY created_at DESC LIMIT 20
    """,
    "admin_failed_images": """
        SELECT id, created_at FROM image_tasks
        WHERE status = 'failed' ORDER BY created_at DESC LIMIT 20
    """,
    "admin_failed_videos": """
        SELECT id, created_at FROM video_tasks
        WHERE status = 'failed' ORDER BY created_at DESC LIMIT 20
    """,
    "today_image_tasks": """
        SELECT count(*) FROM image_tasks WHERE created_at >= now() - interval '1 day'
    """,
    "today_video_tasks": """
        SELECT count(*) FROM video_tasks WHERE created_at >= now() - interval '1 day'
    """,
}


def parse_args():
    default_url = make_url(DATABASE_URL).set(database="shangtu_perf")
    parser = argparse.ArgumentParser(description="Profile task queries in an isolated database")
    parser.add_argument(
        "--database-url",
        default=os.getenv("PERF_DATABASE_URL", default_url.render_as_string(hide_password=False)),
    )
    parser.add_argument("--image-tasks", type=int, default=50000)
    parser.add_argument("--video-tasks", type=int, default=30000)
    parser.add_argument("--max-ms", type=float, default=100.0)
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[1] / ".cache" / "performance" / "task_queries.json"),
    )
    parser.add_argument("--keep-database", action="store_true")
    return parser.parse_args()


async def create_database(url):
    database = url.database or ""
    if not DATABASE_NAME_PATTERN.fullmatch(database):
        raise ValueError("性能数据库名称必须以 _perf 结尾")
    admin_url = url.set(database="postgres")
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database}
        )
        if not exists:
            await connection.execute(text(f'CREATE DATABASE "{database}"'))
    await engine.dispose()


async def drop_database(url):
    database = url.database or ""
    admin_url = url.set(database="postgres")
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as connection:
        await connection.execute(
            text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :name"),
            {"name": database},
        )
        await connection.execute(text(f'DROP DATABASE IF EXISTS "{database}"'))
    await engine.dispose()


async def seed_data(connection, image_count: int, video_count: int):
    await connection.execute(
        text("""
            INSERT INTO users (username, email, password_hash, credits, role, status, created_at)
            SELECT 'perf_' || i, 'perf_' || i || '@example.test', 'test', 10000,
                   'user', 'active', now() - ((i % 90) * interval '1 day')
            FROM generate_series(1, 500) AS i
        """)
    )
    await connection.execute(
        text("""
            INSERT INTO generation_jobs
                (id, user_id, scenario, title, status, archived, created_at, updated_at)
            SELECT lpad(i::text, 32, '0'), ((i - 1) % 500) + 1,
                   CASE WHEN i % 3 = 0 THEN 'digital_human' ELSE 'product_image' END,
                   'Performance job ' || i, 'done', false,
                   now() - ((i % 90) * interval '1 day'), now()
            FROM generate_series(1, 10000) AS i
        """)
    )
    await connection.execute(
        text("""
            INSERT INTO image_tasks
                (id, user_id, job_id, type_id, title, sort_order, prompt, size,
                 status, result_url, progress, provider, credit_cost, credit_refunded,
                 archived, created_at)
            SELECT 'i-' || lpad(i::text, 30, '0'), ((i - 1) % 500) + 1,
                   lpad((((i - 1) % 10000) + 1)::text, 32, '0'), 'main', 'Image ' || i,
                   0, 'prompt', '1024x1024',
                   CASE WHEN i % 20 = 0 THEN 'failed'
                        WHEN i % 5 = 0 THEN 'processing' ELSE 'done' END,
                   CASE WHEN i % 5 = 0 THEN NULL ELSE 'https://example.test/image.png' END,
                   CASE WHEN i % 5 = 0 THEN 50 ELSE 100 END,
                   'fake', 1, false, false,
                   now() - ((i % 90) * interval '1 day')
            FROM generate_series(1, :count) AS i
        """),
        {"count": image_count},
    )
    await connection.execute(
        text("""
            INSERT INTO video_tasks
                (id, user_id, job_id, scenario, type_id, title, sort_order, prompt,
                 input_mode, duration, resolution, aspect_ratio, status, result_url,
                 progress, provider, credit_cost, credit_refunded, archived, created_at)
            SELECT 'v-' || lpad(i::text, 30, '0'), ((i - 1) % 500) + 1,
                   lpad((((i - 1) % 10000) + 1)::text, 32, '0'),
                   CASE WHEN i % 3 = 0 THEN 'digital_human' ELSE 'product_video' END,
                   'standard', 'Video ' || i, 0, 'prompt', 'video', 5, '1080p', '9:16',
                   CASE WHEN i % 20 = 0 THEN 'failed'
                        WHEN i % 5 = 0 THEN 'processing' ELSE 'done' END,
                   CASE WHEN i % 5 = 0 THEN NULL ELSE 'https://example.test/video.mp4' END,
                   CASE WHEN i % 5 = 0 THEN 50 ELSE 100 END,
                   'fake', 10, false, false,
                   now() - ((i % 90) * interval '1 day')
            FROM generate_series(1, :count) AS i
        """),
        {"count": video_count},
    )
    await connection.execute(text("ANALYZE"))


def collect_nodes(plan):
    nodes = [plan]
    for child in plan.get("Plans", []):
        nodes.extend(collect_nodes(child))
    return nodes


async def explain_queries(connection):
    results = {}
    for name, query in QUERIES.items():
        raw = await connection.scalar(
            text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
        )
        payload = json.loads(raw) if isinstance(raw, str) else raw
        root = payload[0]
        nodes = collect_nodes(root["Plan"])
        results[name] = {
            "execution_ms": root["Execution Time"],
            "planning_ms": root["Planning Time"],
            "node_types": sorted({node["Node Type"] for node in nodes}),
            "sequential_scans": sorted(
                {
                    node.get("Relation Name")
                    for node in nodes
                    if node["Node Type"] == "Seq Scan" and node.get("Relation Name")
                }
            ),
        }
    return results


async def set_candidate_indexes(connection, *, create: bool):
    for name, definition in INDEXES.items():
        statement = (
            f'CREATE INDEX "{name}" ON {definition}'
            if create
            else f'DROP INDEX IF EXISTS "{name}"'
        )
        await connection.execute(text(statement))
    await connection.execute(text("ANALYZE"))


async def profile(args):
    url = make_url(args.database_url)
    await create_database(url)
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
            await set_candidate_indexes(connection, create=False)
            await seed_data(connection, args.image_tasks, args.video_tasks)
            baseline = await explain_queries(connection)
            await set_candidate_indexes(connection, create=True)
            optimized = await explain_queries(connection)

        report = {
            "dataset": {"image_tasks": args.image_tasks, "video_tasks": args.video_tasks},
            "max_execution_ms": args.max_ms,
            "baseline": baseline,
            "optimized": optimized,
        }
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        violations = [
            name for name, result in optimized.items() if result["execution_ms"] > args.max_ms
        ]
        for name, result in optimized.items():
            print(
                f"{name}: {baseline[name]['execution_ms']:.2f}ms -> "
                f"{result['execution_ms']:.2f}ms; seq={result['sequential_scans']}"
            )
        if violations:
            raise RuntimeError(f"查询超过 {args.max_ms:g}ms: {', '.join(violations)}")
        print(f"report={output}")
    finally:
        await engine.dispose()
        if not args.keep_database:
            await drop_database(url)


if __name__ == "__main__":
    asyncio.run(profile(parse_args()))
