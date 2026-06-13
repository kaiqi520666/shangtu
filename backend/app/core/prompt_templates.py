from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PromptTemplate


@dataclass(slots=True)
class PromptTemplateLookupResult:
    templates: list[PromptTemplate]
    content: str


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _priority(template: PromptTemplate) -> int:
    flags = (bool(template.scenario), bool(template.platform), bool(template.type_id))
    order = {
        (False, False, False): 0,
        (True, False, False): 1,
        (False, True, False): 2,
        (False, False, True): 3,
        (True, True, False): 4,
        (True, False, True): 5,
        (False, True, True): 6,
        (True, True, True): 7,
    }
    return order[flags]


async def get_prompt_templates(
    db: AsyncSession,
    *,
    scenario: str | None = None,
    purpose: str,
    platform: str | None = None,
    type_id: str | None = None,
    model: str,
) -> PromptTemplateLookupResult:
    """Return active prompt templates matching exact values or generic NULL fallbacks."""

    scenario = _normalize_optional(scenario)
    platform = _normalize_optional(platform)
    type_id = _normalize_optional(type_id)
    purpose = purpose.strip()
    model = model.strip()
    if not purpose:
        raise ValueError("purpose不能为空")
    if not model:
        raise ValueError("model不能为空")

    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.active == True,  # noqa: E712
            PromptTemplate.purpose == purpose,
            PromptTemplate.model == model,
            or_(PromptTemplate.scenario.is_(None), PromptTemplate.scenario == scenario),
            or_(PromptTemplate.platform.is_(None), PromptTemplate.platform == platform),
            or_(PromptTemplate.type_id.is_(None), PromptTemplate.type_id == type_id),
        )
    )
    templates = list(result.scalars().all())
    templates.sort(
        key=lambda item: (
            _priority(item),
            item.version,
            item.created_at,
            item.id,
        )
    )

    content = "\n\n".join(template.content.strip() for template in templates if template.content.strip())
    return PromptTemplateLookupResult(templates=templates, content=content)
