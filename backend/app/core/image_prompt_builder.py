from __future__ import annotations

from dataclasses import dataclass
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.prompt_templates import get_prompt_templates
from app.models import GenerationJob

IMAGE_GENERATE_MODEL = "gpt-image-2"


@dataclass(slots=True)
class ImagePromptBuildResult:
    final_prompt: str
    system_prompt_snapshot: str
    task_prompt_snapshot: str
    user_prompt: str
    prompt_template_refs_json: str


def _parse_json_object(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _template_refs(templates) -> str:
    return json.dumps(
        [
            {
                "id": template.id,
                "name": template.name,
                "scenario": template.scenario,
                "purpose": template.purpose,
                "platform": template.platform,
                "type_id": template.type_id,
                "model": template.model,
                "version": template.version,
            }
            for template in templates
        ],
        ensure_ascii=False,
    )


def _format_task_prompt(
    *,
    settings: dict,
    job: GenerationJob,
    type_id: str | None,
    title: str | None,
) -> str:
    platform = str(settings.get("platform") or "").strip() or "未指定"
    language = str(settings.get("language") or "").strip() or "中文"
    ratio = str(settings.get("ratio") or "").strip() or "未指定"
    product_input = (job.input_text or "").strip()
    lines = [
        f"【投放平台】{platform}",
        f"【排版语言】{language}",
        f"【画面比例】{ratio}",
        f"【图类型】{title or type_id or '商品套图'}",
        "【商品卖点与要求】",
        product_input,
        "【强约束】禁止虚构品牌 Logo、认证标识、价格、销量、参数等无法从参考图与上述卖点确认的信息；如需添加文字必须使用上述指定语言，文字简洁清晰，适合电商平台展示。",
    ]
    return "\n".join(line for line in lines if line)


def _split_templates_by_type(templates, type_id: str | None) -> tuple[list, list]:
    type_templates = [
        template
        for template in templates
        if template.type_id and template.type_id == type_id
    ]
    system_templates = [template for template in templates if not template.type_id]
    return system_templates, type_templates


async def build_product_suite_image_prompt(
    db: AsyncSession,
    *,
    job: GenerationJob,
    type_id: str | None,
    title: str | None,
    user_prompt: str | None,
) -> ImagePromptBuildResult:
    if not type_id or not type_id.strip():
        raise ValueError("商品套图生成缺少图种类型")

    type_id = type_id.strip()
    settings = _parse_json_object(job.settings_json)
    platform = str(settings.get("platform") or "").strip() or None

    lookup = await get_prompt_templates(
        db,
        scenario=job.scenario,
        purpose="image_generate",
        platform=platform,
        type_id=type_id,
        model=IMAGE_GENERATE_MODEL,
    )
    system_templates, type_templates = _split_templates_by_type(lookup.templates, type_id)
    system_prompt = "\n\n".join(
        template.content.strip()
        for template in system_templates
        if template.content and template.content.strip()
    )
    default_user_prompt = "\n\n".join(
        template.content.strip()
        for template in type_templates
        if template.content and template.content.strip()
    )
    effective_user_prompt = (user_prompt or "").strip() or default_user_prompt
    if not effective_user_prompt:
        raise ValueError("未找到当前图种的默认提示词，请检查提示词模板配置")
    task_prompt = _format_task_prompt(
        settings=settings,
        job=job,
        type_id=type_id,
        title=title,
    )

    final_parts = [
        "【系统提示词】",
        system_prompt,
        "【任务提示词】",
        task_prompt,
        "【用户提示词】",
        effective_user_prompt,
    ]
    final_prompt = "\n".join(part for part in final_parts if part)

    return ImagePromptBuildResult(
        final_prompt=final_prompt,
        system_prompt_snapshot=system_prompt,
        task_prompt_snapshot=task_prompt,
        user_prompt=effective_user_prompt,
        prompt_template_refs_json=_template_refs(lookup.templates),
    )
