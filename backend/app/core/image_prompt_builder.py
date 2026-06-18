from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import dump_json, parse_json_object
from app.core.prompt_templates import get_prompt_templates
from app.models import GenerationJob

IMAGE_GENERATE_MODEL = "gpt-image-2"
VIDEO_GENERATE_MODEL = "seedance-2"
QWEN_TEXT_MODEL = "qwen3.6-flash"


@dataclass(slots=True)
class ImagePromptBuildResult:
    final_prompt: str
    system_prompt_snapshot: str
    task_prompt_snapshot: str
    user_prompt: str
    prompt_template_refs_json: str


@dataclass(slots=True)
class VideoPromptBuildResult:
    final_prompt: str
    system_prompt_snapshot: str
    task_prompt_snapshot: str
    user_prompt: str
    prompt_template_refs_json: str


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


def compose_video_prompt(
    *,
    system_prompt: str | None,
    task_prompt: str | None,
    user_prompt: str | None,
) -> str:
    final_parts = [
        "【系统提示词】",
        (system_prompt or "").strip(),
        "【视频任务提示词】",
        (task_prompt or "").strip(),
        "【用户提示词】",
        (user_prompt or "").strip(),
    ]
    return "\n".join(part for part in final_parts if part)


def _template_refs(templates) -> str:
    return dump_json(
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
        ]
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
            "【强约束】只生成一位模特；不要换服装；不要改变模特主体身份特征；不要虚构品牌 Logo、价格、促销文字、认证标识或无法确认的信息。",
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


def _split_templates_by_type(templates, type_id: str | None) -> tuple[list, list]:
    type_templates = [
        template
        for template in templates
        if template.type_id and template.type_id == type_id
    ]
    system_templates = [template for template in templates if not template.type_id]
    return system_templates, type_templates


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
    product_requirement = (user_prompt or "").strip()
    if default_user_prompt and product_requirement:
        effective_user_prompt = (
            f"{default_user_prompt}\n\n"
            "【商品卖点与视频要求】\n"
            f"{product_requirement}"
        )
    else:
        effective_user_prompt = product_requirement or default_user_prompt
    if not effective_user_prompt:
        raise ValueError("未找到当前图种的默认提示词，请检查提示词模板配置")
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
        system_prompt_snapshot=system_prompt,
        task_prompt_snapshot=task_prompt,
        user_prompt=effective_user_prompt,
        prompt_template_refs_json=_template_refs(lookup.templates),
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

    platform = str(settings.get("platform") or settings.get("market") or "").strip() or None
    language = str(settings.get("language") or "").strip() or "未指定"
    aspect_ratio = str(settings.get("aspect_ratio") or settings.get("aspectRatio") or "").strip() or "未指定"
    resolution = str(settings.get("resolution") or "").strip() or "未指定"
    duration = str(settings.get("duration") or "").strip() or "未指定"
    input_mode = str(settings.get("input_mode") or settings.get("inputMode") or "").strip() or "未指定"

    lookup = await get_prompt_templates(
        db,
        scenario="product_video",
        purpose="video_generate",
        platform=platform,
        type_id=type_id,
        model=VIDEO_GENERATE_MODEL,
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
        raise ValueError("未找到当前视频方向的默认提示词，请检查提示词模板配置")

    task_prompt = "\n".join(
        line
        for line in [
            "【任务】生成一条电商商品短视频。",
            f"【视频方向】{title or type_id}",
            f"【投放市场/平台】{platform or '未指定'}",
            f"【语言/声音】{language}",
            f"【画面比例】{aspect_ratio}",
            f"【清晰度】{resolution}",
            f"【时长】{duration}秒",
            f"【参考素材模式】{input_mode}",
            "【强约束】保持用户上传商品图里的主体、颜色、材质、结构和核心外观一致；不要虚构品牌 Logo、认证、价格、销量或无法确认的参数。",
        ]
        if line
    )

    final_prompt = compose_video_prompt(
        system_prompt=system_prompt,
        task_prompt=task_prompt,
        user_prompt=effective_user_prompt,
    )

    return VideoPromptBuildResult(
        final_prompt=final_prompt,
        system_prompt_snapshot=system_prompt,
        task_prompt_snapshot=task_prompt,
        user_prompt=effective_user_prompt,
        prompt_template_refs_json=_template_refs(lookup.templates),
    )


async def build_ai_write_prompt(
    db: AsyncSession,
    *,
    scenario: str | None,
    platform: str | None,
) -> str:
    lookup = await get_prompt_templates(
        db,
        scenario=scenario,
        purpose="ai_write",
        platform=platform,
        type_id=None,
        model=QWEN_TEXT_MODEL,
    )
    content = lookup.content.strip()
    if not content:
        return ""
    dynamic = f"当前投放平台：{platform or '未指定'}"
    return "\n\n".join(part for part in [content, dynamic] if part)


async def build_product_image_strategy_template_prompt(
    db: AsyncSession,
    *,
    platform: str | None,
) -> str:
    lookup = await get_prompt_templates(
        db,
        scenario="product_image",
        purpose="strategy",
        platform=platform,
        type_id=None,
        model=QWEN_TEXT_MODEL,
    )
    return lookup.content.strip()
