from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.prompt_snapshot import build_prompt_snapshot


@dataclass(slots=True)
class VideoPromptBuildResult:
    final_prompt: str
    prompt_snapshot: dict


async def build_video_generate_prompt(
    db: AsyncSession,
    *,
    type_id: str,
    title: str | None,
    user_prompt: str | None,
    settings: dict,
) -> VideoPromptBuildResult:
    type_id = (type_id or "").strip()
    if not type_id:
        raise ValueError("视频生成缺少视频方向")

    effective_user_prompt = (user_prompt or "").strip()
    if not effective_user_prompt:
        raise ValueError("请先生成并确认视频提示词")

    return VideoPromptBuildResult(
        final_prompt=effective_user_prompt,
        prompt_snapshot=build_prompt_snapshot(
            system="",
            task="",
            user=effective_user_prompt,
            final=effective_user_prompt,
            template_refs=[],
        ),
    )
