import json
import os
import re
import traceback

import httpx
from dotenv import load_dotenv
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()

APIYI_KEY = os.getenv("APIYI_KEY")
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

engine = create_async_engine(os.getenv("DATABASE_URL"))
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def update_task_in_db(task_id: str, status: str, result_url: str | None = None):
    from app.models import ImageTask

    async with SessionLocal() as session:
        await session.execute(
            update(ImageTask)
            .where(ImageTask.id == task_id)
            .values(status=status, result_url=result_url)
        )
        await session.commit()


async def generate_image(ctx, task_id: str, prompt: str, size: str = "720x1280"):
    redis = ctx["redis"]

    try:
        await redis.set(f"task:{task_id}:status", "processing", ex=7200)
        transport = httpx.AsyncHTTPTransport(proxy=None)

        async with httpx.AsyncClient(timeout=310, transport=transport) as client:
            resp = await client.post(
                "https://api.apiyi.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {APIYI_KEY}"},
                json={
                    "model": "gpt-image-2-vip",
                    "size": size,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            result = resp.json()
            print(f"apiyi 原始响应: {result}")

        if "data" in result:
            url = result["data"][0].get("url") or result["data"][0].get("b64_json")
        elif "choices" in result:
            content = result["choices"][0]["message"]["content"]
            match = re.search(r"!\[image\]\((https?://[^\)]+)\)", content)
            url = match.group(1) if match else None
        else:
            url = None

        if url:
            await redis.set(
                f"task:{task_id}:result",
                json.dumps({"url": url}),
                ex=86400,
            )
            await redis.set(f"task:{task_id}:status", "done", ex=86400)
            await update_task_in_db(task_id, "done", url)
        else:
            await redis.set(f"task:{task_id}:status", "failed", ex=3600)
            await redis.set(f"task:{task_id}:error", "无法提取图片URL", ex=3600)
            await update_task_in_db(task_id, "failed")

    except httpx.TimeoutException:
        await redis.set(f"task:{task_id}:status", "timeout", ex=3600)
        await update_task_in_db(task_id, "timeout")
    except Exception as e:
        print(f"任务失败详细错误: {e}")
        traceback.print_exc()
        await redis.set(f"task:{task_id}:status", "failed", ex=3600)
        await redis.set(f"task:{task_id}:error", str(e), ex=3600)
        await update_task_in_db(task_id, "failed")