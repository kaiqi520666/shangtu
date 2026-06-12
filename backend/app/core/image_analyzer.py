import json
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()

DASHSCOPE_MODEL = "qwen3.6-flash"

PRODUCT_IMAGE_MODULES = {
    "first-screen": {
        "name": "首屏主视觉",
        "desc": "极简大图与大字报，第一眼传递核心卖点价值。",
        "strategy": "大标题聚焦，高饱和度背板突显商品核心形态。",
    },
    "core-selling": {
        "name": "核心卖点图",
        "desc": "突出商品三大硬核优势，多点对照打消疑虑。",
        "strategy": "三栏目清单排版，配图层级鲜明。",
    },
    "use-scenario": {
        "name": "使用场景图",
        "desc": "呈现真实使用状态或家居融入。",
        "strategy": "融合淡雅环境投影，拉近用户心理距离。",
    },
    "multi-angle": {
        "name": "多角度呈现图",
        "desc": "展示侧面、背面及折叠等完整外观。",
        "strategy": "三视图对齐，透视比例精准缩放。",
    },
    "ambient-scene": {
        "name": "场景氛围图",
        "desc": "强光影写实渲染，增强商品的高级质感。",
        "strategy": "暖色调逆光底板，配合微小阴影质感。",
    },
    "detail-zoom": {
        "name": "商品细节图",
        "desc": "局部放大，精细展现材质和精湛工艺。",
        "strategy": "中心放大镜切割圆圈，拉线批注。",
    },
    "brand-story": {
        "name": "品牌故事图",
        "desc": "传达品牌匠心，突显高档商品格调。",
        "strategy": "英文点缀，加宽留白，典雅无衬线排版。",
    },
    "specs-info": {
        "name": "尺寸/规格/容量图",
        "desc": "直观标注物理尺寸与对比参照物。",
        "strategy": "添加标注线与比例尺，数值一目了然。",
    },
    "contrast-effect": {
        "name": "效果对比图",
        "desc": "使用前/后、升级前/后的直观效果。",
        "strategy": "双栏垂直切割，BEFORE / AFTER 徽章强对抗。",
    },
    "tech-specs": {
        "name": "详细规格/参数表",
        "desc": "将复杂工业数据整合为超清美化表格。",
        "strategy": "圆角半透明卡片表格，结构化突出核心。",
    },
    "manufacturing": {
        "name": "工艺制作图",
        "desc": "展示精密做工、材质层级拆解。",
        "strategy": "爆炸视图效果，精细拆解元器件架构。",
    },
    "freebies": {
        "name": "配件/赠品图",
        "desc": "明确告知用户收货拆箱的丰富组合。",
        "strategy": "买即送角贴，配全套礼盒全家福。",
    },
    "series-show": {
        "name": "系列展示图",
        "desc": "多配色、多SKU合辑呈现，极大提升加购。",
        "strategy": "多色环绕渐变，卡片式并列。",
    },
    "ingredients": {
        "name": "商品成分图",
        "desc": "透明呈现成分比例或纯净配料表。",
        "strategy": "分子网格配图，科学健康风骨。",
    },
    "warranty": {
        "name": "售后保障图",
        "desc": "官方质保、包邮无忧、金牌认证退换。",
        "strategy": "醒目信任徽章，构建消费安全感。",
    },
    "usage-tips": {
        "name": "使用建议图",
        "desc": "温馨提示使用建议、充电与养护说明。",
        "strategy": "简洁图标列表，避免售后客诉纠纷。",
    },
}


class DashScopeConfigError(RuntimeError):
    pass


def get_dashscope_endpoint() -> str:
    base_url = os.getenv("DASHSCOPE_URL")
    if not base_url:
        raise DashScopeConfigError("DASHSCOPE_URL未配置")

    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def get_dashscope_api_key() -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise DashScopeConfigError("DASHSCOPE_API_KEY未配置")
    return api_key


def build_product_prompt(platform: str) -> str:
    return f"""你是电商商品图分析助手。
请根据图片内容，识别商品类型、外观、材质、用途、适用人群、核心卖点和可用于商品主图生成的关键信息。

当前投放平台：{platform or '未指定'}


请严格按以下格式输出，不要输出 markdown，不要输出解释，不要输出多余标题。
如果图片中无法确定某项，请基于商品外观做谨慎推测，不要编造具体品牌、认证、型号或无法从图片判断的参数。

1.产品名称：
2.核心卖点：
3.适用人群：
4.期望场景：
5.具体参数："""


def build_product_image_strategy_prompt(
    *,
    platform: str,
    language: str,
    product_input: str,
    modules: list[dict],
) -> str:
    modules_text = "\n".join(
        [
            (
                f"{index}. id={item['id']}，name={item['name']}，"
                f"用途={item['desc']}，默认策略={item['strategy']}"
            )
            for index, item in enumerate(modules, start=1)
        ]
    )
    module_ids = [item["id"] for item in modules]

    return f"""你是资深电商详情页策划和视觉总监。
请结合用户上传的商品图片、用户填写的商品卖点要求，以及用户选择的详情页图种，生成一组可编辑的详情页模块策略。

当前投放平台：{platform or '未指定'}
排版语言：{language or '中文'}

用户商品卖点与要求：
{product_input}

用户选择的图种，必须按以下顺序生成：
{modules_text}

输出要求：
1. 只输出 JSON，不要 markdown，不要解释，不要代码块。
2. modules 数量必须等于用户选择图种数量，顺序必须一致。
3. 每个模块 id 必须来自这个列表：{json.dumps(module_ids, ensure_ascii=False)}
4. 不要编造品牌 Logo、认证、价格、销量、型号、具体参数；如果图片和卖点中没有明确依据，只做谨慎表达。
5. content 是给前端 textarea 展示和后续生图 prompt 使用的内容，使用短行文本，每行一个要点。
6. 文案要适合电商详情页，不要过度夸张，不要医疗、功效、绝对化承诺。

JSON 格式：
{{
  "brief": "一句话概括本次详情页策略",
  "modules": [
    {{
      "id": "first-screen",
      "moduleName": "首屏主视觉",
      "title": "首屏 3 秒内传达核心价值",
      "strategy": "大标题聚焦，高饱和度背板突显商品核心形态。",
      "content": "模块序号：1\\n主标题：...\\n副标题：...\\n画面层级：..."
    }}
  ]
}}"""


async def analyze_product_image(
    *,
    image_url: str,
    platform: str = "",
) -> str:
    if not image_url.startswith(("http://", "https://")):
        raise ValueError("image_url必须是可访问的HTTP地址")

    payload = {
        "model": DASHSCOPE_MODEL,
        "enable_thinking": False,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url},
                    },
                    {
                        "type": "text",
                        "text": build_product_prompt(platform),
                    },
                ],
            }
        ],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            get_dashscope_endpoint(),
            headers={"Authorization": f"Bearer {get_dashscope_api_key()}"},
            json=payload,
        )

    if response.status_code >= 400:
        raise RuntimeError(f"DashScope请求失败: {response.status_code} {response.text[:300]}")

    result = response.json()
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("DashScope响应格式异常") from exc

    if not content or not content.strip():
        raise RuntimeError("DashScope未返回有效内容")

    return content.strip()


def _selected_product_image_modules(module_ids: list[str]) -> list[dict]:
    if not module_ids:
        raise ValueError("请至少选择一个生成图种")

    selected: list[dict] = []
    seen: set[str] = set()
    unsupported: list[str] = []
    for module_id in module_ids:
        if module_id in seen:
            continue
        module = PRODUCT_IMAGE_MODULES.get(module_id)
        if not module:
            unsupported.append(module_id)
            continue
        selected.append({"id": module_id, **module})
        seen.add(module_id)

    if unsupported:
        raise ValueError(f"存在不支持的图种：{', '.join(unsupported)}")
    if not selected:
        raise ValueError("请至少选择一个生成图种")
    return selected


def _parse_json_response(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise RuntimeError("DashScope未返回有效JSON")
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise RuntimeError("DashScope返回的策略JSON格式异常") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("DashScope返回的策略JSON格式异常")
    return parsed


def _stringify_content(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    return ""


def _fallback_module_content(module: dict, index: int) -> str:
    return "\n".join(
        [
            f"模块序号：{index + 1}",
            f"模块目标：{module['desc']}",
            f"排版策略：{module['strategy']}",
            "视觉重点：突出商品主体，减少无效装饰，保持电商平台可读性。",
        ]
    )


def _normalize_strategy_response(parsed: dict, selected_modules: list[dict]) -> dict:
    raw_modules = parsed.get("modules")
    if not isinstance(raw_modules, list):
        raw_modules = []

    raw_by_id = {
        item.get("id"): item for item in raw_modules if isinstance(item, dict) and item.get("id")
    }
    modules = []
    for index, module in enumerate(selected_modules):
        raw = raw_by_id.get(module["id"]) or {}
        content = _stringify_content(raw.get("content"))
        modules.append(
            {
                "id": module["id"],
                "moduleName": module["name"],
                "title": _stringify_content(raw.get("title"))
                or f"{module['name']}策略",
                "strategy": _stringify_content(raw.get("strategy"))
                or module["strategy"],
                "content": content or _fallback_module_content(module, index),
            }
        )

    brief = _stringify_content(parsed.get("brief")) or (
        f"已根据商品图片、卖点和平台规则生成 {len(modules)} 个详情页模块策略。"
    )
    return {"brief": brief, "modules": modules}


async def generate_product_image_strategy(
    *,
    image_url: str,
    platform: str = "",
    language: str = "中文",
    product_input: str = "",
    module_ids: list[str],
) -> dict:
    if not image_url.startswith(("http://", "https://")):
        raise ValueError("image_url必须是可访问的HTTP地址")

    normalized_input = product_input.strip()
    if not normalized_input:
        raise ValueError("请先填写商品卖点与要求")

    selected_modules = _selected_product_image_modules(module_ids)
    prompt = build_product_image_strategy_prompt(
        platform=platform,
        language=language,
        product_input=normalized_input[:4000],
        modules=selected_modules,
    )

    payload = {
        "model": DASHSCOPE_MODEL,
        "enable_thinking": False,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url},
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    }

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            get_dashscope_endpoint(),
            headers={"Authorization": f"Bearer {get_dashscope_api_key()}"},
            json=payload,
        )

    if response.status_code >= 400:
        raise RuntimeError(f"DashScope请求失败: {response.status_code} {response.text[:300]}")

    result = response.json()
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("DashScope响应格式异常") from exc

    if not content or not content.strip():
        raise RuntimeError("DashScope未返回有效内容")

    parsed = _parse_json_response(content)
    return _normalize_strategy_response(parsed, selected_modules)
