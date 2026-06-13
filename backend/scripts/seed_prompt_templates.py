from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.prompt_templates import get_prompt_templates  # noqa: E402
from app.core.time import utc_now  # noqa: E402
from app.models import PromptTemplate  # noqa: E402
import app.models  # noqa: E402,F401


PRODUCT_SUITE_TYPES = [
    {
        "type_id": "white-bg",
        "name": "商品套图-白底图默认用户提示词",
        "content": "生成白底商品图：纯净浅色或白色背景，商品主体居中完整展示，轮廓清晰，光影自然，适合作为电商主图。",
    },
    {
        "type_id": "scene",
        "name": "商品套图-场景图默认用户提示词",
        "content": "生成真实使用场景图：围绕商品用途构建可信场景，保持商品主体准确，强化购买代入感，避免喧宾夺主。",
    },
    {
        "type_id": "selling-point",
        "name": "商品套图-卖点图默认用户提示词",
        "content": "生成卖点展示图：突出商品核心优势，信息层级清晰，可加入简洁文字信息块，但不得虚构品牌、认证、价格、销量或无法确认的参数。",
    },
    {
        "type_id": "detail",
        "name": "商品套图-细节图默认用户提示词",
        "content": "生成商品细节图：展示材质、结构、功能或工艺细节，可使用局部放大、标注线和简洁说明，帮助用户理解商品品质。",
    },
]


PRODUCT_IMAGE_TYPES = [
    ("first-screen", "首屏主视觉", "用首屏大图和清晰标题，在第一眼传达商品核心价值。"),
    ("core-selling", "核心卖点图", "围绕三到五个核心卖点组织画面，突出商品优势和购买理由。"),
    ("use-scenario", "使用场景图", "呈现商品真实使用状态或空间融入效果，增强用户代入感。"),
    ("multi-angle", "多角度呈现图", "展示商品正面、侧面、背面或关键形态变化，保证比例和透视准确。"),
    ("ambient-scene", "场景氛围图", "通过光影、材质和环境氛围提升商品质感，但商品主体仍需清晰可辨。"),
    ("detail-zoom", "商品细节图", "用局部放大、拉线批注或特写方式展示材质、接口、纹理、工艺等细节。"),
    ("brand-story", "品牌故事图", "表达品牌调性、使用理念或品质感，不虚构品牌历史、认证或官方背书。"),
    ("specs-info", "尺寸/规格/容量图", "用标注线、比例尺或结构化信息表达尺寸、容量、规格等已知信息。"),
    ("contrast-effect", "效果对比图", "呈现使用前后、升级前后或普通款与升级款的对比关系，避免绝对化承诺。"),
    ("tech-specs", "详细规格/参数表", "将明确可确认的参数整理成清晰表格或信息面板，不补造未知参数。"),
    ("manufacturing", "工艺制作图", "展示材质层级、制作工艺或结构拆解，画面专业但不夸大工艺来源。"),
    ("freebies", "配件/赠品图", "展示包装、配件或赠品组合，仅展示用户明确提供或图片中可确认的内容。"),
    ("series-show", "系列展示图", "展示多颜色、多规格或系列组合，未提供 SKU 时不要虚构具体款式。"),
    ("ingredients", "商品成分图", "清晰展示成分、材质或配料信息，只使用用户输入中确认的内容。"),
    ("warranty", "售后保障图", "表达售后、质保或服务信息时必须基于用户提供内容，不虚构官方承诺。"),
    ("usage-tips", "使用建议图", "以简洁图标或步骤说明展示使用、保养、安装或注意事项。"),
]


def _template_rows() -> list[dict]:
    rows: list[dict] = [
        {
            "scenario": None,
            "purpose": "image_generate",
            "platform": None,
            "type_id": None,
            "model": "gpt-image-2",
            "name": "生图通用主体一致规则",
            "content": (
                "你是专业电商商品图生成助手。必须以用户提供的参考商品图为主体，保持商品的款式、颜色、材质、"
                "结构和核心外观一致；只允许根据用户要求调整背景、构图、光影、场景和信息排版。"
                "不要虚构品牌 Logo、认证、参数、价格、销量或无法从图片与用户文字确认的信息。"
                "若需要添加文字，必须使用用户指定语言，文字简洁清晰，适合电商平台展示。"
            ),
        },
        {
            "scenario": None,
            "purpose": "image_generate",
            "platform": "亚马逊",
            "type_id": None,
            "model": "gpt-image-2",
            "name": "亚马逊-生图平台规则",
            "content": (
                "亚马逊平台素材应突出商品本身，画面干净可信，避免夸张促销元素、虚构徽章、虚构认证、"
                "价格、销量和误导性对比。主图倾向清爽背景，卖点图和详情模块需保持信息简洁可读。"
            ),
        },
        {
            "scenario": "product_suite",
            "purpose": "image_generate",
            "platform": None,
            "type_id": None,
            "model": "gpt-image-2",
            "name": "商品套图-生图场景规则",
            "content": (
                "生成一张电商商品套图素材。根据当前图类型完成对应画面，不要生成整张详情长图；"
                "同一批套图应保持商品主体一致、视觉风格统一、信息表达克制。"
            ),
        },
        {
            "scenario": "product_image",
            "purpose": "image_generate",
            "platform": None,
            "type_id": None,
            "model": "gpt-image-2",
            "name": "商品详情图-生图场景规则",
            "content": (
                "生成一张电商商品详情页模块图，不要生成整张长详情页。画面应有清晰模块主题、合理信息层级，"
                "文字简洁，适合放入详情页中连续浏览。"
            ),
        },
        {
            "scenario": None,
            "purpose": "ai_write",
            "platform": None,
            "type_id": None,
            "model": "qwen3.6-flash",
            "name": "AI帮写-通用读图规则",
            "content": (
                "你是电商商品图分析助手。请根据图片内容识别商品类型、外观、材质、用途、适用人群、核心卖点，"
                "并输出可用于后续商品图生成的关键信息。不要编造具体品牌、认证、型号或无法从图片判断的参数。"
            ),
        },
        {
            "scenario": None,
            "purpose": "ai_write",
            "platform": "亚马逊",
            "type_id": None,
            "model": "qwen3.6-flash",
            "name": "亚马逊-AI帮写平台规则",
            "content": (
                "分析结果应偏向亚马逊商品页表达：强调商品核心属性、材质、尺寸/规格依据、适用场景和用户利益点，"
                "避免夸大宣传、绝对化承诺和无依据认证。"
            ),
        },
        {
            "scenario": "product_suite",
            "purpose": "ai_write",
            "platform": None,
            "type_id": None,
            "model": "qwen3.6-flash",
            "name": "商品套图-AI帮写输出格式",
            "content": (
                "请严格按以下格式输出，不要输出 markdown，不要输出解释，不要输出多余标题。\n\n"
                "1.产品名称：\n2.核心卖点：\n3.适用人群：\n4.期望场景：\n5.具体参数："
            ),
        },
        {
            "scenario": "product_image",
            "purpose": "ai_write",
            "platform": None,
            "type_id": None,
            "model": "qwen3.6-flash",
            "name": "商品详情图-AI帮写输出格式",
            "content": (
                "请严格按以下格式输出，不要输出 markdown，不要输出解释，不要输出多余标题。内容要便于后续拆成详情页模块。\n\n"
                "1.产品名称：\n2.核心卖点：\n3.适用人群：\n4.期望场景：\n5.具体参数："
            ),
        },
        {
            "scenario": "product_image",
            "purpose": "strategy",
            "platform": None,
            "type_id": None,
            "model": "qwen3.6-flash",
            "name": "商品详情图-策略生成规则",
            "content": (
                "你是资深电商详情页策划和视觉总监。请结合用户上传的商品图片、用户填写的商品卖点要求，"
                "以及用户选择的详情页图种，生成一组可编辑的详情页模块策略。只输出 JSON，不要 markdown，"
                "modules 数量必须等于用户选择图种数量，顺序必须一致；不要编造品牌 Logo、认证、价格、销量、型号、具体参数。"
            ),
        },
        {
            "scenario": "product_image",
            "purpose": "strategy",
            "platform": "亚马逊",
            "type_id": None,
            "model": "qwen3.6-flash",
            "name": "亚马逊-详情图策略平台规则",
            "content": (
                "详情页策略应符合亚马逊商品页常见表达：信息克制、证据充分、避免夸张促销和无依据背书，"
                "优先突出商品属性、场景、规格、细节和使用利益点。"
            ),
        },
    ]

    for item in PRODUCT_SUITE_TYPES:
        rows.append(
            {
                "scenario": "product_suite",
                "purpose": "image_generate",
                "platform": None,
                "type_id": item["type_id"],
                "model": "gpt-image-2",
                "name": item["name"],
                "content": item["content"],
            }
        )

    for type_id, module_name, content in PRODUCT_IMAGE_TYPES:
        rows.append(
            {
                "scenario": "product_image",
                "purpose": "image_generate",
                "platform": None,
                "type_id": type_id,
                "model": "gpt-image-2",
                "name": f"商品详情图-{module_name}默认用户提示词",
                "content": content,
            }
        )

    return rows


def _normalized_row(row: dict) -> dict:
    normalized = {
        "scenario": row.get("scenario") or None,
        "purpose": str(row["purpose"]).strip(),
        "platform": row.get("platform") or None,
        "type_id": row.get("type_id") or None,
        "model": str(row["model"]).strip(),
        "name": str(row["name"]).strip(),
        "content": str(row["content"]).strip(),
        "version": int(row.get("version") or 1),
        "active": bool(row.get("active", True)),
    }
    if not normalized["purpose"]:
        raise ValueError("purpose不能为空")
    if not normalized["model"]:
        raise ValueError("model不能为空")
    if not normalized["name"]:
        raise ValueError("name不能为空")
    if not normalized["content"]:
        raise ValueError(f"{normalized['name']} content不能为空")
    return normalized


def _exact_filter(row: dict):
    filters = [
        PromptTemplate.purpose == row["purpose"],
        PromptTemplate.model == row["model"],
        PromptTemplate.name == row["name"],
        PromptTemplate.version == row["version"],
    ]
    for field_name in ("scenario", "platform", "type_id"):
        column = getattr(PromptTemplate, field_name)
        value = row[field_name]
        filters.append(column.is_(None) if value is None else column == value)
    return filters


async def upsert_templates() -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    unchanged = 0
    rows = [_normalized_row(row) for row in _template_rows()]

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        for row in rows:
            result = await db.execute(
                select(PromptTemplate).where(*_exact_filter(row)).limit(1)
            )
            template = result.scalar_one_or_none()
            if template is None:
                db.add(PromptTemplate(**row))
                inserted += 1
                continue

            changed = False
            for field_name in ("content", "active"):
                value = row[field_name]
                if getattr(template, field_name) != value:
                    setattr(template, field_name, value)
                    changed = True

            if changed:
                template.updated_at = utc_now()
                updated += 1
            else:
                unchanged += 1

        await db.commit()

    return inserted, updated, unchanged


async def verify_lookup() -> None:
    async with SessionLocal() as db:
        result = await get_prompt_templates(
            db,
            scenario="product_suite",
            purpose="image_generate",
            platform="亚马逊",
            type_id="white-bg",
            model="gpt-image-2",
        )
        names = [template.name for template in result.templates]
        required = {
            "生图通用主体一致规则",
            "亚马逊-生图平台规则",
            "商品套图-生图场景规则",
            "商品套图-白底图默认用户提示词",
        }
        missing = required - set(names)
        if missing:
            raise RuntimeError(f"提示词模板查询缺少: {', '.join(sorted(missing))}")

        fallback = await get_prompt_templates(
            db,
            scenario="product_suite",
            purpose="image_generate",
            platform="不存在的平台",
            type_id="white-bg",
            model="gpt-image-2",
        )
        fallback_names = [template.name for template in fallback.templates]
        if "亚马逊-生图平台规则" in fallback_names:
            raise RuntimeError("平台不匹配时不应返回亚马逊模板")
        if "生图通用主体一致规则" not in fallback_names:
            raise RuntimeError("平台不匹配时应回退通用生图模板")

        print("lookup order:", " -> ".join(names))
        print("fallback order:", " -> ".join(fallback_names))


async def main() -> None:
    inserted, updated, unchanged = await upsert_templates()
    await verify_lookup()
    print(
        "prompt templates seeded:",
        f"inserted={inserted}",
        f"updated={updated}",
        f"unchanged={unchanged}",
    )


if __name__ == "__main__":
    asyncio.run(main())
