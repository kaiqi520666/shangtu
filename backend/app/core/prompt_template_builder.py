from sqlalchemy.ext.asyncio import AsyncSession

from app.core.model_config import QWEN_TEXT_MODEL
from app.core.prompt_templates import get_prompt_templates


async def build_ai_write_prompt(
    db: AsyncSession,
    *,
    scenario: str | None,
    platform: str | None,
    type_id: str | None = None,
) -> str:
    lookup = await get_prompt_templates(
        db,
        scenario=scenario,
        purpose="ai_write",
        platform=platform,
        type_id=type_id,
        model=QWEN_TEXT_MODEL,
    )
    content = lookup.content.strip()
    if not content:
        return ""
    dynamic = f"当前投放平台：{platform or '未指定'}"
    return "\n\n".join(part for part in [content, dynamic] if part)


async def build_strategy_template_prompt(
    db: AsyncSession,
    *,
    scenario: str,
    platform: str | None,
    type_id: str | None = None,
) -> str:
    lookup = await get_prompt_templates(
        db,
        scenario=scenario,
        purpose="strategy",
        platform=platform,
        type_id=type_id,
        model=QWEN_TEXT_MODEL,
    )
    return lookup.content.strip()
