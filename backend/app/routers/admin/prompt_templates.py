from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.time import utc_now
from app.models import PromptTemplate, User
from app.schemas.response import Response, fail, success

from .schemas import PromptTemplateRequest
from .utils import audit_log, page_payload, prompt_template_payload

router = APIRouter()

VALID_SCENARIOS = {"product_suite", "product_image", "outfit", "free_image", "product_video"}
VALID_PURPOSES = {"image_generate", "ai_write", "strategy"}


@router.get("/prompt-templates", response_model=Response)
async def list_prompt_templates(
    page: int = 1,
    page_size: int = 20,
    scenario: str | None = None,
    purpose: str | None = None,
    model: str | None = None,
    type_id: str | None = None,
    active: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = []
    if scenario:
        if scenario == "__global__":
            conditions.append(PromptTemplate.scenario.is_(None))
        elif scenario in VALID_SCENARIOS:
            conditions.append(PromptTemplate.scenario == scenario)
    if purpose in VALID_PURPOSES:
        conditions.append(PromptTemplate.purpose == purpose)
    if model:
        conditions.append(PromptTemplate.model == model.strip())
    if type_id:
        cleaned_type_id = type_id.strip()
        if cleaned_type_id == "__global__":
            conditions.append(PromptTemplate.type_id.is_(None))
        elif cleaned_type_id:
            conditions.append(PromptTemplate.type_id == cleaned_type_id)
    if active in {"true", "false"}:
        conditions.append(PromptTemplate.active == (active == "true"))
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                PromptTemplate.name.ilike(like),
                PromptTemplate.content.ilike(like),
                PromptTemplate.platform.ilike(like),
                PromptTemplate.type_id.ilike(like),
                PromptTemplate.model.ilike(like),
            )
        )

    total_stmt = select(func.count()).select_from(PromptTemplate)
    data_stmt = select(PromptTemplate).order_by(
        PromptTemplate.updated_at.desc(),
        PromptTemplate.created_at.desc(),
        PromptTemplate.id.desc(),
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)

    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [prompt_template_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, page, page_size))


@router.post("/prompt-templates", response_model=Response)
async def create_prompt_template(
    req: PromptTemplateRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = _normalize_prompt_template(req)
    except ValueError as exc:
        return fail(str(exc))

    template = PromptTemplate(**data)
    db.add(template)
    await db.flush()
    db.add(
        audit_log(
            current_admin,
            "create_prompt_template",
            "prompt_template",
            template.id,
            {
                "name": template.name,
                "scenario": template.scenario,
                "purpose": template.purpose,
                "model": template.model,
            },
        )
    )
    await db.commit()
    await db.refresh(template)
    return success(prompt_template_payload(template))


@router.patch("/prompt-templates/{template_id}", response_model=Response)
async def update_prompt_template(
    template_id: str,
    req: PromptTemplateRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PromptTemplate).where(PromptTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        return fail("提示词模板不存在")

    try:
        data = _normalize_prompt_template(req)
    except ValueError as exc:
        return fail(str(exc))

    for key, value in data.items():
        setattr(template, key, value)
    template.updated_at = utc_now()
    db.add(
        audit_log(
            current_admin,
            "update_prompt_template",
            "prompt_template",
            template.id,
            {
                "name": template.name,
                "scenario": template.scenario,
                "purpose": template.purpose,
                "model": template.model,
                "active": template.active,
            },
        )
    )
    await db.commit()
    await db.refresh(template)
    return success(prompt_template_payload(template))


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_prompt_template(req: PromptTemplateRequest) -> dict:
    scenario = _clean_optional(req.scenario)
    purpose = req.purpose.strip()
    platform = _clean_optional(req.platform)
    type_id = _clean_optional(req.type_id)
    model = req.model.strip()
    name = req.name.strip()
    content = req.content.strip()

    if scenario and scenario not in VALID_SCENARIOS:
        raise ValueError("场景不支持")
    if purpose not in VALID_PURPOSES:
        raise ValueError("用途不支持")
    if not model:
        raise ValueError("模型不能为空")
    if not name:
        raise ValueError("模板名称不能为空")
    if not content:
        raise ValueError("提示词内容不能为空")

    return {
        "scenario": scenario,
        "purpose": purpose,
        "platform": platform,
        "type_id": type_id,
        "model": model,
        "name": name,
        "content": content,
        "version": req.version,
        "active": req.active,
    }
