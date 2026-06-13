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


PLATFORM_RULES = {
    "亚马逊": {
        "image_generate": (
            "亚马逊平台素材应突出商品本身，主图倾向纯白或极浅背景，商品完整清晰、占画面主体。"
            "避免文字、Logo、水印、促销贴纸、边框、拼接图、虚构徽章、虚构认证、价格、销量和误导性对比。"
            "辅图可展示场景、比例、功能、配件和细节，但必须与实际售卖商品一致。"
        ),
        "ai_write": (
            "分析结果应偏向亚马逊商品页表达：强调商品核心属性、材质、尺寸/规格依据、适用场景和用户利益点，"
            "避免夸大宣传、绝对化承诺、医疗功效、无依据认证和无法从图片判断的型号参数。"
        ),
        "strategy": (
            "详情页策略应符合亚马逊商品页常见表达：信息克制、证据充分、画面专业，"
            "优先安排主视觉、核心卖点、使用场景、尺寸规格、细节特写和配件展示，避免促销化和无依据背书。"
        ),
    },
    "淘宝天猫1688": {
        "image_generate": (
            "淘宝、天猫、1688 平台素材应清晰展示商品主体，主图避免牛皮癣式大面积文字、水印、杂乱拼接和过度促销。"
            "可根据图种加入适量卖点文字、场景和细节标注，但文字必须简短易读，商品主体不能被遮挡。"
        ),
        "ai_write": (
            "分析结果应适合国内电商货架表达：突出材质、功能、适用人群、使用场景、规格和采购决策信息，"
            "不要编造品牌授权、检测报告、销量、价格、产地或无法确认的参数。"
        ),
        "strategy": (
            "详情图策略应兼顾转化和可读性：先展示核心利益点，再补充场景、细节、规格、对比和使用说明。"
            "允许清晰卖点文字和信息块，但避免满屏文字、低质促销贴和遮挡商品主体。"
        ),
    },
    "Temu": {
        "image_generate": (
            "Temu 素材应简洁、明亮、商品居中清晰。主图优先白色或中性背景；附图展示多角度、尺寸感、材质细节、"
            "包装/配件和生活化使用场景。避免复杂背景、水印、夸张促销、虚构认证和与实物不一致的装饰。"
        ),
        "ai_write": (
            "分析结果应偏向跨境高性价比平台表达：提炼材质、颜色、尺寸、功能、适用场景、包装内容和用户直接关心的问题，"
            "不要编造认证、库存、价格或平台活动。"
        ),
        "strategy": (
            "详情图策略应快速解释商品价值：首屏明确商品用途，随后展示核心卖点、多角度、尺寸规格、细节和生活场景。"
            "文案短、视觉直接，适合移动端快速浏览。"
        ),
    },
    "TikTok Shop": {
        "image_generate": (
            "TikTok Shop 素材应适合移动端货架浏览，第一张图清楚展示商品正面，避免水印、边框、促销文字、模糊和重复角度。"
            "附图可展示不同角度、功能、配件和真实使用场景，画面要有短视频电商的直观吸引力。"
        ),
        "ai_write": (
            "分析结果应突出短平快卖点、使用场景、开箱内容、用户痛点和适合短视频展示的视觉亮点，"
            "避免夸大承诺、无依据功效和平台外引流信息。"
        ),
        "strategy": (
            "详情图策略应移动端优先：首屏直接说明商品是什么和核心好处，后续模块用场景、细节、配件、对比和使用步骤快速建立信任。"
            "文字少而有力，避免复杂长段落。"
        ),
    },
    "拼多多": {
        "image_generate": (
            "拼多多素材应突出商品和核心利益点，画面清晰、对比强、信息直观。避免低质拼接、水印、过多促销字、虚构价格、虚构销量和误导性对比。"
            "卖点图可更直接，但必须保持商品主体清楚可辨。"
        ),
        "ai_write": (
            "分析结果应提炼高感知卖点：规格、数量、材质、用途、适用人群、家庭/日常场景和购买理由，"
            "不要编造价格优势、补贴、销量、官方认证或无法确认的信息。"
        ),
        "strategy": (
            "详情图策略应强调清楚、直接、易比较：核心卖点、规格容量、使用场景、细节、包装清单和注意事项。"
            "画面可有醒目信息块，但避免杂乱和遮挡主体。"
        ),
    },
    "抖音电商": {
        "image_generate": (
            "抖音电商素材应真实清晰展示商品。第一张主图必须突出实物主体，避免无关水印、边框、牛皮癣式文字、拼接图、模糊和遮挡。"
            "其他图可展示正面、试用/试穿场景、细节、颜色规格和白底图，适合移动端浏览。"
        ),
        "ai_write": (
            "分析结果应适合内容电商表达：突出商品正面特征、场景价值、细节亮点、规格颜色和用户痛点，"
            "避免引流信息、绝对化承诺、虚构功效、虚构认证和无法确认的参数。"
        ),
        "strategy": (
            "详情图策略应有短视频电商节奏：首屏强识别，随后用场景、卖点、细节、规格和使用建议建立信任。"
            "文字简洁醒目，避免满屏文字和遮挡商品。"
        ),
    },
    "OZON": {
        "image_generate": (
            "OZON 素材应与商品名称和描述一致，商品完整展示、彩色、清晰、无遮挡。主图突出实际售卖商品，"
            "避免不相关道具、水印、低质图片、误导性文字和与商品无关的 Logo。"
        ),
        "ai_write": (
            "分析结果应偏向俄语区跨境货架信息：突出商品类型、材质、功能、规格、使用场景、包装内容和注意事项，"
            "不要编造品牌、认证、原产地、保修或技术参数。"
        ),
        "strategy": (
            "详情图策略应清晰解释商品是什么、适合谁、怎么用、有什么规格和细节。"
            "优先安排主视觉、多角度、材质/结构、尺寸规格、使用场景和包装清单。"
        ),
    },
    "独立站": {
        "image_generate": (
            "独立站素材可以更品牌化和生活方式化，但仍需保证商品主体准确清晰。"
            "主图应建立可信第一印象；场景图可强化品牌调性、生活方式、细节质感和转化氛围。"
            "避免虚构品牌背书、奖项、认证、价格和评价。"
        ),
        "ai_write": (
            "分析结果应兼顾品牌表达和转化：提炼商品定位、核心卖点、目标人群、场景故事、材质细节和可用于落地页的价值主张，"
            "不要编造品牌历史或用户评价。"
        ),
        "strategy": (
            "详情图策略可采用品牌落地页结构：首屏价值主张、生活方式场景、核心卖点、细节证明、规格说明、使用步骤和信任信息。"
            "风格可更有品牌感，但信息必须基于图片和用户输入。"
        ),
    },
    "Shopee": {
        "image_generate": (
            "Shopee 素材应高亮、清晰、聚焦商品，封面图尽量使用干净背景和明确主体，避免模糊、杂乱、水印和重复角度。"
            "附图展示不同颜色、角度、使用场景、细节和包装内容，适合东南亚移动端浏览。"
        ),
        "ai_write": (
            "分析结果应面向移动端快速购物：突出商品用途、规格、颜色、材质、场景、包装内容和买家关心的实际利益，"
            "避免无依据认证、夸张功效和不可验证的销量价格。"
        ),
        "strategy": (
            "详情图策略应清楚、轻量、移动端友好：首屏主卖点、场景图、细节图、规格图、颜色/款式展示和使用建议。"
            "文字短句化，信息块清晰。"
        ),
    },
    "阿里国际站": {
        "image_generate": (
            "阿里国际站素材应适合 B2B 采购判断：商品主体清晰，展示规格、材质、结构、应用场景、包装和可定制信息。"
            "避免过度零售化促销、水印、虚构认证、虚构工厂资质和无法确认的参数。"
        ),
        "ai_write": (
            "分析结果应突出 B2B 采购信息：产品名称、材质、规格、功能、应用行业、包装/配件、可定制点和采购关注点，"
            "不要编造认证、产能、MOQ、工厂资质或测试报告。"
        ),
        "strategy": (
            "详情图策略应服务采购决策：产品总览、核心参数、材质工艺、细节结构、应用场景、包装清单、定制能力提示和质量控制说明。"
            "只使用已知或用户提供的信息。"
        ),
    },
    "速卖通": {
        "image_generate": (
            "速卖通素材应面向跨境零售，商品主体清晰、背景干净，附图展示多角度、细节、规格尺寸、使用场景和包装内容。"
            "避免水印、虚构品牌、虚构认证、夸张促销和与实物不一致的效果。"
        ),
        "ai_write": (
            "分析结果应适合跨境买家理解：提炼商品用途、材质、规格、颜色、兼容性、使用场景和包装内容，"
            "避免本地化无法确认的信息和无依据参数。"
        ),
        "strategy": (
            "详情图策略应降低跨境理解成本：首屏说明商品用途，随后展示核心卖点、尺寸规格、细节、兼容/适用范围、场景和包装。"
            "文案简洁，适合多语言翻译。"
        ),
    },
    "SHEIN": {
        "image_generate": (
            "SHEIN 素材应偏时尚、年轻、移动端友好。服饰类重点展示版型、颜色、材质、上身/搭配场景和细节；非服饰也应保持潮流感和干净构图。"
            "避免虚构品牌、虚构尺码、过度修饰导致与实物不符。"
        ),
        "ai_write": (
            "分析结果应关注时尚属性：版型、颜色、材质、适用季节、穿搭/使用场景、细节设计和目标人群，"
            "不要编造尺码、品牌系列、面料成分或模特信息。"
        ),
        "strategy": (
            "详情图策略应突出穿搭和细节：首屏风格定位、上身/场景展示、面料纹理、版型细节、颜色款式、尺寸提示和搭配建议。"
            "保持年轻化、轻量化、移动端阅读友好。"
        ),
    },
    "京东": {
        "image_generate": (
            "京东素材应专业、清晰、可信，主图突出商品主体，避免水印、杂乱拼接、夸张促销、虚构价格、虚构认证和遮挡主体。"
            "详情图可强调品质、参数、功能、售后保障和使用场景，但必须基于已确认信息。"
        ),
        "ai_write": (
            "分析结果应偏向品质和可信决策：突出商品属性、功能、规格、材质、适用场景、细节和售后/保障信息的可确认部分，"
            "不要编造京东自营、质保、认证或销量。"
        ),
        "strategy": (
            "详情图策略应有清晰的品质感和参数表达：核心卖点、功能场景、细节工艺、规格参数、使用步骤和保障信息。"
            "不确定的信息不要写成确定承诺。"
        ),
    },
    "美客多": {
        "image_generate": (
            "美客多素材应清晰、对焦准确、光线充足，商品是画面中心。主图建议干净背景，附图可展示场景、比例、纹理、细节和使用方式。"
            "避免模糊、水印、无关文字、误导性道具和与商品不一致的展示。"
        ),
        "ai_write": (
            "分析结果应适合拉美电商买家：突出商品类型、用途、规格、材质、尺寸感、使用场景和细节，"
            "避免虚构品牌、认证、价格、保修和无依据承诺。"
        ),
        "strategy": (
            "详情图策略应帮助买家快速判断：主视觉、核心卖点、尺寸/规格、细节、使用场景、包装内容和注意事项。"
            "画面保持清晰、自然、可信。"
        ),
    },
    "Coupang": {
        "image_generate": (
            "Coupang 素材应简洁、清晰、商品主体突出。主图建议干净背景和完整商品，详情图可图文结合展示功能、参数、场景和配件。"
            "避免水印、夸张促销、虚构认证、虚构品牌背书和与实际商品不符的元素。"
        ),
        "ai_write": (
            "分析结果应适合韩国电商货架：突出商品功能、材质、规格、颜色、包装内容、使用场景和用户利益点，"
            "不要编造认证、保修、配送承诺或参数。"
        ),
        "strategy": (
            "详情图策略应结构化展示：主视觉、核心功能、规格参数、材质细节、使用场景、包装清单和使用说明。"
            "文字简短，适合移动端浏览。"
        ),
    },
    "Wayfair": {
        "image_generate": (
            "Wayfair 素材应高质感、清晰、适合家居/生活方式场景。主图展示商品完整外观，附图展示空间搭配、尺寸感、材质纹理、细节和使用情境。"
            "避免低清、强水印、夸张促销文字、虚构材质和与商品不符的空间比例。"
        ),
        "ai_write": (
            "分析结果应偏向家居和生活方式采购：提炼风格、材质、颜色、尺寸感、适用空间、功能、搭配建议和细节质感，"
            "不要编造品牌、设计师背书、材质成分或认证。"
        ),
        "strategy": (
            "详情图策略应建立空间想象和购买信心：完整主图、场景搭配、尺寸比例、材质纹理、结构细节、功能展示和空间建议。"
            "画面有质感但信息真实。"
        ),
    },
}


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
    ]

    for platform, rules in PLATFORM_RULES.items():
        rows.extend(
            [
                {
                    "scenario": None,
                    "purpose": "image_generate",
                    "platform": platform,
                    "type_id": None,
                    "model": "gpt-image-2",
                    "name": f"{platform}-生图平台规则",
                    "content": rules["image_generate"],
                },
                {
                    "scenario": None,
                    "purpose": "ai_write",
                    "platform": platform,
                    "type_id": None,
                    "model": "qwen3.6-flash",
                    "name": f"{platform}-AI帮写平台规则",
                    "content": rules["ai_write"],
                },
                {
                    "scenario": "product_image",
                    "purpose": "strategy",
                    "platform": platform,
                    "type_id": None,
                    "model": "qwen3.6-flash",
                    "name": f"{platform}-详情图策略平台规则",
                    "content": rules["strategy"],
                },
            ]
        )

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
        for platform in PLATFORM_RULES:
            for purpose, model, scenario in (
                ("image_generate", "gpt-image-2", None),
                ("ai_write", "qwen3.6-flash", None),
                ("strategy", "qwen3.6-flash", "product_image"),
            ):
                check = await get_prompt_templates(
                    db,
                    scenario=scenario,
                    purpose=purpose,
                    platform=platform,
                    type_id=None,
                    model=model,
                )
                if not any(template.platform == platform for template in check.templates):
                    raise RuntimeError(f"{platform} 缺少 {purpose} 平台模板")

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
