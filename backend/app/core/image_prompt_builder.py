from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import dump_json, parse_json_object
from app.core.model_config import IMAGE_GENERATE_MODEL, QWEN_TEXT_MODEL
from app.core.prompt_snapshot import build_prompt_snapshot
from app.core.prompt_templates import get_prompt_templates
from app.models import GenerationJob


@dataclass(slots=True)
class ImagePromptBuildResult:
    final_prompt: str
    prompt_snapshot: dict


@dataclass(slots=True)
class VideoPromptBuildResult:
    final_prompt: str
    prompt_snapshot: dict


def compose_image_prompt(
    *,
    system_prompt: str | None,
    task_prompt: str | None,
    user_prompt: str | None,
) -> str:
    final_parts = [
        "【系统提示词】",
        (system_prompt or "").strip(),
        "【任务提示词】",
        (task_prompt or "").strip(),
        "【用户提示词】",
        (user_prompt or "").strip(),
    ]
    return "\n".join(part for part in final_parts if part)


def _template_refs(templates) -> list[dict]:
    return [
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
    ]


def _template_refs_json(templates) -> str:
    return dump_json(_template_refs(templates))


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
    if job.scenario == "product_image":
        task_lines = [
            "【任务】生成一张电商商品详情页模块图，不要生成整张长详情页。",
            f"【详情图模块】{title or type_id or '详情图'}",
        ]
    elif job.scenario == "outfit":
        scene_description = str(settings.get("sceneDescription") or "").strip()
        selected_model_name = str(settings.get("selectedModelName") or "").strip()
        model_suffix = f"，模特名称：{selected_model_name}" if selected_model_name else ""
        extra_requirement = (
            product_input if product_input and product_input != scene_description else ""
        )
        lines = [
            "【任务】生成一张服饰穿搭图。",
            f"【拍摄场景】{title or type_id or '服饰穿搭场景'}",
            f"【投放平台】{platform}",
            f"【排版语言】{language}",
            f"【画面比例】{ratio}",
            scene_description
            and f"【自定义场景要求】{scene_description}",
            "【服装要求】保持用户上传服装图的颜色、版型、材质、图案和核心外观一致。",
            f"【模特要求】使用用户选择的模特图作为人物参考{model_suffix}。",
            extra_requirement and "【补充要求】",
            extra_requirement,
            "【强约束】只生成一位模特；不要换服装；不要改变模特主体身份特征；不要虚构品牌 Logo、价格、促销文字、认证标识或无法确认的信息；如需添加文字必须使用上述指定语言，文字简洁清晰，适合电商平台展示。",
        ]
        return "\n".join(line for line in lines if line)
    else:
        task_lines = [
            "【任务】生成一张电商商品套图素材。",
            f"【图类型】{title or type_id or '商品套图'}",
        ]

    lines = [
        *task_lines,
        f"【投放平台】{platform}",
        f"【排版语言】{language}",
        f"【画面比例】{ratio}",
        "【商品卖点与要求】",
        product_input,
        "【强约束】禁止虚构品牌 Logo、认证标识、价格、销量、参数等无法从参考图与上述卖点确认的信息；如需添加文字必须使用上述指定语言，文字简洁清晰，适合电商平台展示。",
    ]
    return "\n".join(line for line in lines if line)


async def build_image_generate_prompt(
    db: AsyncSession,
    *,
    job: GenerationJob,
    type_id: str | None,
    title: str | None,
    user_prompt: str | None,
) -> ImagePromptBuildResult:
    if not type_id or not type_id.strip():
        raise ValueError("图片生成缺少图种类型")

    type_id = type_id.strip()
    settings = parse_json_object(job.settings_json)
    platform = str(settings.get("platform") or "").strip() or None

    lookup = await get_prompt_templates(
        db,
        scenario=job.scenario,
        purpose="image_generate",
        platform=platform,
        type_id=None,
        model=IMAGE_GENERATE_MODEL,
    )
    system_prompt = "\n\n".join(
        template.content.strip()
        for template in lookup.templates
        if template.content and template.content.strip()
    )
    effective_user_prompt = (user_prompt or "").strip()
    if not effective_user_prompt:
        raise ValueError("请先生成并确认图片策略")
    task_prompt = _format_task_prompt(
        settings=settings,
        job=job,
        type_id=type_id,
        title=title,
    )

    final_prompt = compose_image_prompt(
        system_prompt=system_prompt,
        task_prompt=task_prompt,
        user_prompt=effective_user_prompt,
    )

    return ImagePromptBuildResult(
        final_prompt=final_prompt,
        prompt_snapshot=build_prompt_snapshot(
            system=system_prompt,
            task=task_prompt,
            user=effective_user_prompt,
            final=final_prompt,
            template_refs=_template_refs(lookup.templates),
        ),
    )


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
        raise ValueError("请先生成并确认视频策略")

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
) -> str:
    lookup = await get_prompt_templates(
        db,
        scenario=scenario,
        purpose="strategy",
        platform=platform,
        type_id=None,
        model=QWEN_TEXT_MODEL,
    )
    return lookup.content.strip()
