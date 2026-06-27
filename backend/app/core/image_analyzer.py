import json
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()

DASHSCOPE_MODEL = "qwen3.6-flash"


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


MULTI_IMAGE_ANALYSIS_RULE = (
    "如果看到多张图片，优先以标注为主图、开始画面或首帧图的图片作为核心分析对象，"
    "其余图片作为细节、角度、配件或场景的辅助参考。"
)


def build_multimodal_image_content(images: list[dict]) -> list[dict]:
    if not images:
        raise ValueError("至少需要一张图片")

    content: list[dict] = []
    for index, item in enumerate(images, start=1):
        url = str(item.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            raise ValueError("图片地址必须是可访问的HTTP地址")
        label = str(item.get("label") or "").strip() or f"图片{index}"
        content.append({"type": "text", "text": f"【{label}】"})
        content.append({"type": "image_url", "image_url": {"url": url}})
    return content


def build_free_image_optimize_prompt(prompt: str) -> str:
    return f"""你是 AI 生图提示词优化助手。
请把用户输入改写成更清晰、更具体、更适合图像生成模型执行的提示词。

要求：
1. 保留用户原意，不要改变主体、物种、商品类型、人物身份或核心动作。
2. 可以补充画面构图、镜头、光线、背景、材质、风格、清晰度等视觉描述。
3. 不要添加用户没有要求的品牌 Logo、文字、水印、价格、促销、认证、销量、具体参数。
4. 不要输出解释，不要输出 Markdown，不要输出标题。
5. 只输出优化后的提示词本身。
6. 如果用户输入已经足够清楚，只做轻微润色。

用户原始提示词：
{prompt}"""


def build_product_image_strategy_prompt(
    *,
    platform: str,
    language: str,
    product_input: str,
    modules: list[dict],
    template_prompt: str | None = None,
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

    base_prompt = template_prompt.strip() if template_prompt else "你是资深电商详情页策划和视觉总监。"

    return f"""{base_prompt}
请结合用户上传的商品图片、用户填写的商品卖点要求，以及用户选择的详情页图种，生成一组可编辑的详情页模块策略。

当前投放平台：{platform or '未指定'}
最终成图文字语言：{language or '中文'}

用户商品卖点与要求：
{product_input}

用户选择的图种，必须按以下顺序生成：
{modules_text}

输出要求：
1. 只输出 JSON，不要 markdown，不要解释，不要代码块。
2. modules 数量必须等于用户选择图种数量，顺序必须一致。
3. 每个模块 id 必须来自这个列表：{json.dumps(module_ids, ensure_ascii=False)}
4. 所有 JSON 字段都必须用中文撰写；最终成图如需文字，会按“最终成图文字语言”翻译呈现。
5. 不要编造品牌 Logo、认证、价格、销量、型号、具体参数；如果图片和卖点中没有明确依据，只做谨慎表达。
6. content 是给前端 textarea 展示和后续生图 prompt 使用的内容，使用短行文本，每行一个要点。
7. 文案要适合电商详情页，不要过度夸张，不要医疗、功效、绝对化承诺。

JSON 格式：
{{
  "brief": "一句话概括本次详情页策略",
  "modules": [
    {{
      "id": "first-screen",
      "moduleName": "首屏主视觉",
      "strategy": "大标题聚焦，高饱和度背板突显商品核心形态。",
      "content": "主标题：...\\n副标题：...\\n画面层级：..."
    }}
  ]
}}"""


def build_product_suite_strategy_prompt(
    *,
    platform: str,
    language: str,
    product_input: str,
    structures: list[dict],
    template_prompt: str | None = None,
) -> str:
    structures_text = "\n".join(
        [
            (
                f"{index}. id={item['id']}，name={item['name']}，count={item['count']}，"
                f"用途={item['desc']}，默认策略={item['strategy']}"
            )
            for index, item in enumerate(structures, start=1)
        ]
    )
    structure_ids = [item["id"] for item in structures]
    base_prompt = template_prompt.strip() if template_prompt else "你是资深电商商品套图策划和视觉总监。"

    return f"""{base_prompt}
请结合用户上传的商品图片、用户填写的商品卖点要求，以及用户选择的套图结构，生成一组可编辑的商品套图策略。

当前投放平台：{platform or '未指定'}
最终成图文字语言：{language or '中文'}

用户商品卖点与要求：
{product_input}

用户选择的套图结构，必须按以下顺序生成：
{structures_text}

输出要求：
1. 只输出 JSON，不要 markdown，不要解释，不要代码块。
2. items 数量必须等于用户选择的套图类型数量，顺序必须一致。
3. 每个 item id 必须来自这个列表：{json.dumps(structure_ids, ensure_ascii=False)}
4. count 必须等于用户选择的数量，不要自行增减。
5. 所有 JSON 字段都必须用中文撰写；最终成图如需文字，会按“最终成图文字语言”翻译呈现。
6. 不要编造品牌 Logo、认证、价格、销量、型号、具体参数；如果图片和卖点中没有明确依据，只做谨慎表达。
7. content 是给前端 textarea 展示和后续生图 prompt 使用的内容，使用短行文本，每行一个要点。
8. 策略要适合电商套图，保证同一批图片商品主体一致、风格统一，但每个套图类型有明确作用。

JSON 格式：
{{
  "brief": "一句话概括本次商品套图策略",
  "items": [
    {{
      "id": "white-bg",
      "name": "白底图",
      "description": "适配平台首图规范，突出商品主体与干净轮廓。",
      "strategy": "纯白或浅灰背景，商品居中完整展示，光影自然。",
      "content": "画面目标：...\\n主体构图：...\\n文字与标注：...",
      "count": 1,
      "enabled": true
    }}
  ]
}}"""


def build_outfit_strategy_prompt(
    *,
    platform: str,
    language: str,
    scene_description: str,
    selected_model_name: str,
    scenes: list[dict],
    template_prompt: str | None = None,
) -> str:
    scenes_text = "\n".join(
        [
            (
                f"{index}. id={item['id']}，name={item['name']}，"
                f"场景目标={item['desc']}，默认策略={item['strategy']}"
            )
            for index, item in enumerate(scenes, start=1)
        ]
    )
    scene_ids = [item["id"] for item in scenes]
    base_prompt = template_prompt.strip() if template_prompt else "你是资深电商服饰穿搭摄影策划和视觉总监。"

    return f"""{base_prompt}
请结合用户上传的服装图、模特参考图、用户选择的拍摄场景，生成一组可编辑的服饰穿搭拍摄策略。

当前投放平台：{platform or '未指定'}
最终成图文字语言：{language or '中文'}
模特名称：{selected_model_name or '未指定'}
用户自定义场景补充：{scene_description or '无'}

用户选择的拍摄场景，必须按以下顺序生成：
{scenes_text}

输出要求：
1. 只输出 JSON，不要 markdown，不要解释，不要代码块。
2. items 数量必须等于用户选择场景数量，顺序必须一致。
3. 每个 item id 必须来自这个列表：{json.dumps(scene_ids, ensure_ascii=False)}
4. 所有 JSON 字段都必须用中文撰写；最终成图如需文字，会按“最终成图文字语言”翻译呈现。
5. content 是给前端 textarea 展示和后续生图 prompt 使用的内容，必须包含“模特姿态”“镜头角度”“服装保真约束”“画面氛围”四段，用户会看到并可编辑。
6. 服装保真约束是硬约束：必须要求保持用户上传服装图的颜色、版型、材质、图案、长度、领口、袖型、廓形和核心外观一致。
7. 不要虚构品牌 Logo、价格、销量、材质成分、认证或图片中无法确认的服装参数。
8. 策略要适合电商穿搭图，主体清晰、真实可信，避免多人物、换衣服、改变服装款式。

JSON 格式：
{{
  "brief": "一句话概括本次穿搭拍摄策略",
  "items": [
    {{
      "id": "street",
      "name": "都市街头",
      "description": "都市街头场景，突出服装的日常穿搭感和街拍质感。",
      "strategy": "自然日光或轻微电影感光影，模特行走或站立。",
      "pose": "模特姿态：...",
      "camera": "镜头角度：...",
      "fidelity": "服装保真约束：...",
      "atmosphere": "画面氛围：...",
      "content": "模特姿态：...\\n镜头角度：...\\n服装保真约束：...\\n画面氛围：..."
    }}
  ]
}}"""


def build_video_strategy_prompt(
    *,
    type_id: str,
    name: str,
    input_mode: str,
    market: str,
    language: str,
    duration: int,
    aspect_ratio: str,
    product_input: str,
    template_prompt: str | None = None,
) -> str:
    base_prompt = template_prompt.strip() if template_prompt else "你是资深电商短视频脚本策划和视觉导演。"
    return f"""{base_prompt}
请结合用户上传的视频素材图、用户选择的视频方向和补充要求，生成一条可编辑的商品视频脚本策略。

视频方向：{name or type_id}
素材模式：{input_mode or '未指定'}
目标市场/平台：{market or '未指定'}
最终成片文字/配音语言：{language or '中文'}
视频时长：{duration}秒
画面比例：{aspect_ratio or '未指定'}

用户补充要求：
{product_input or '无'}

输出要求：
1. 只输出 JSON，不要 markdown，不要解释，不要代码块。
2. items 固定 1 条，id 必须等于 {json.dumps(type_id, ensure_ascii=False)}。
3. 所有 JSON 字段都必须用中文撰写；最终成片如需文字或配音，会按“最终成片文字/配音语言”翻译呈现。
4. content 是给用户编辑和后续生视频 prompt 使用的完整脚本，必须按 {duration} 秒时长规划镜头节奏，建议拆成 2-4 个时间段（如 0-2 秒、2-4 秒、4-{duration} 秒）。
5. content 里要明确写出：成片如需出现文字或配音，必须使用“{language or '中文'}”；如果用户选择纯音乐无口播，则不要安排口播，只保留画面文字或无文字镜头。
6. content 要覆盖开场、镜头运动、卖点呈现、画面风格和避免事项，但不要拆成多个 JSON 字段。
7. 不要编造品牌 Logo、认证、价格、销量、型号、具体参数；如果素材和补充要求中没有明确依据，只做谨慎表达。
8. 策略要适合电商短视频，节奏清晰，主体稳定，商品外观一致，避免无意义镜头和过度夸张表达。

JSON 格式：
{{
  "brief": "一句话概括本次视频脚本方向",
  "items": [
    {{
      "id": "{type_id}",
      "name": "{name or type_id}",
      "content": "0-2秒：...\\n2-4秒：...\\n4-{duration}秒：...\\n文字/配音语言：...\\n避免事项：..."
    }}
  ]
}}"""


async def analyze_product_image(
    *,
    images: list[dict],
    platform: str = "",
    prompt: str | None = None,
) -> str:
    final_prompt = "\n\n".join(
        part
        for part in [
            prompt or build_product_prompt(platform),
            MULTI_IMAGE_ANALYSIS_RULE,
        ]
        if part
    )
    content = build_multimodal_image_content(images)
    content.append({"type": "text", "text": final_prompt})

    payload = {
        "model": DASHSCOPE_MODEL,
        "enable_thinking": False,
        "messages": [
            {
                "role": "user",
                "content": content,
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


async def optimize_free_image_prompt(prompt: str) -> str:
    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise ValueError("请输入需要优化的提示词")

    payload = {
        "model": DASHSCOPE_MODEL,
        "enable_thinking": False,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": build_free_image_optimize_prompt(normalized_prompt[:4000]),
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


def _catalog_by_id(catalog: list[dict]) -> dict[str, dict]:
    return {str(item.get("id") or "").strip(): item for item in catalog if item.get("id")}


def _selected_product_image_modules(module_ids: list[str], catalog: list[dict]) -> list[dict]:
    if not module_ids:
        raise ValueError("请至少选择一个生成图种")

    catalog_by_id = _catalog_by_id(catalog)
    selected: list[dict] = []
    seen: set[str] = set()
    unsupported: list[str] = []
    for module_id in module_ids:
        module_id = str(module_id or "").strip()
        if not module_id or module_id in seen:
            continue
        module = catalog_by_id.get(module_id)
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


def _selected_product_suite_structures(structure: list[dict], catalog: list[dict]) -> list[dict]:
    if not structure:
        raise ValueError("请至少选择一个套图类型")

    catalog_by_id = _catalog_by_id(catalog)
    selected: list[dict] = []
    seen: set[str] = set()
    unsupported: list[str] = []
    for item in structure:
        if not isinstance(item, dict):
            continue
        structure_id = str(item.get("id") or "").strip()
        if not structure_id or structure_id in seen:
            continue
        config = catalog_by_id.get(structure_id)
        if not config:
            unsupported.append(structure_id)
            continue
        enabled = bool(item.get("enabled", True))
        if not enabled:
            seen.add(structure_id)
            continue
        default_count = int(config.get("default_count") or 1)
        max_count = int(config.get("max_count") or default_count)
        try:
            count = int(item.get("count", default_count))
        except (TypeError, ValueError):
            raise ValueError(f"{config['name']}数量无效")
        if count < 1 or count > max_count:
            raise ValueError(f"{config['name']}数量必须在 1-{max_count} 张之间")
        selected.append(
            {
                "id": structure_id,
                "name": config["name"],
                "desc": config["desc"],
                "strategy": config["strategy"],
                "count": count,
                "enabled": True,
            }
        )
        seen.add(structure_id)

    if unsupported:
        raise ValueError(f"存在不支持的套图类型：{', '.join(unsupported)}")
    if not selected:
        raise ValueError("请至少选择一个套图类型")
    return selected


def _selected_outfit_scenes(scene_ids: list[str], catalog: list[dict]) -> list[dict]:
    if not scene_ids:
        raise ValueError("请至少选择一个拍摄场景")

    catalog_by_id = _catalog_by_id(catalog)
    selected: list[dict] = []
    seen: set[str] = set()
    unsupported: list[str] = []
    for scene_id in scene_ids:
        scene_id = str(scene_id or "").strip()
        if not scene_id or scene_id in seen:
            continue
        scene = catalog_by_id.get(scene_id)
        if not scene:
            unsupported.append(scene_id)
            continue
        selected.append({"id": scene_id, **scene})
        seen.add(scene_id)

    if unsupported:
        raise ValueError(f"存在不支持的拍摄场景：{', '.join(unsupported)}")
    if not selected:
        raise ValueError("请至少选择一个拍摄场景")
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
            f"模块目标：{module['desc']}",
            f"排版策略：{module['strategy']}",
            "视觉重点：突出商品主体，减少无效装饰，保持电商平台可读性。",
        ]
    )


def _fallback_suite_content(item: dict, index: int) -> str:
    return "\n".join(
        [
            f"画面目标：{item['desc']}",
            f"视觉策略：{item['strategy']}",
            f"生成数量：{item['count']} 张",
            "统一要求：保持商品主体、颜色、材质和核心外观一致，文字信息清晰克制。",
        ]
    )


def _fallback_outfit_content(scene: dict, index: int) -> str:
    return "\n".join(
        [
            "模特姿态：自然站立或轻微动态姿势，肢体舒展，完整展示服装版型。",
            "镜头角度：中景到全身构图，镜头略低或平视，保证服装比例自然。",
            "服装保真约束：保持上传服装的颜色、版型、材质、图案、长度、领口、袖型、廓形和核心外观一致，不换款不改款。",
            f"画面氛围：{scene['strategy']}",
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
                "strategy": _stringify_content(raw.get("strategy"))
                or module["strategy"],
                "content": content or _fallback_module_content(module, index),
            }
        )

    brief = _stringify_content(parsed.get("brief")) or (
        f"已根据商品图片、卖点和平台规则生成 {len(modules)} 个详情页模块策略。"
    )
    return {"brief": brief, "modules": modules}


def _normalize_suite_strategy_response(parsed: dict, selected_structures: list[dict]) -> dict:
    raw_items = parsed.get("items")
    if not isinstance(raw_items, list):
        raw_items = []

    raw_by_id = {item.get("id"): item for item in raw_items if isinstance(item, dict) and item.get("id")}
    items = []
    for index, structure in enumerate(selected_structures):
        raw = raw_by_id.get(structure["id"]) or {}
        content = _stringify_content(raw.get("content"))
        items.append(
            {
                "id": structure["id"],
                "name": structure["name"],
                "description": _stringify_content(raw.get("description")) or structure["desc"],
                "strategy": _stringify_content(raw.get("strategy")) or structure["strategy"],
                "content": content or _fallback_suite_content(structure, index),
                "count": structure["count"],
                "enabled": True,
            }
        )

    brief = _stringify_content(parsed.get("brief")) or (
        f"已根据商品图片、卖点和平台规则生成 {len(items)} 个套图类型策略。"
    )
    return {"brief": brief, "items": items}


def _normalize_outfit_strategy_response(parsed: dict, selected_scenes: list[dict]) -> dict:
    raw_items = parsed.get("items")
    if not isinstance(raw_items, list):
        raw_items = []

    raw_by_id = {item.get("id"): item for item in raw_items if isinstance(item, dict) and item.get("id")}
    items = []
    for index, scene in enumerate(selected_scenes):
        raw = raw_by_id.get(scene["id"]) or {}
        content = _stringify_content(raw.get("content"))
        pose = _stringify_content(raw.get("pose"))
        camera = _stringify_content(raw.get("camera"))
        fidelity = _stringify_content(raw.get("fidelity"))
        atmosphere = _stringify_content(raw.get("atmosphere"))
        if not content:
            content = "\n".join(
                part
                for part in [pose, camera, fidelity, atmosphere]
                if part
            )
        items.append(
            {
                "id": scene["id"],
                "name": scene["name"],
                "description": _stringify_content(raw.get("description")) or scene["desc"],
                "strategy": _stringify_content(raw.get("strategy")) or scene["strategy"],
                "pose": pose,
                "camera": camera,
                "fidelity": fidelity,
                "atmosphere": atmosphere,
                "content": content or _fallback_outfit_content(scene, index),
            }
        )

    brief = _stringify_content(parsed.get("brief")) or (
        f"已根据服装图、模特参考和场景配置生成 {len(items)} 个穿搭拍摄策略。"
    )
    return {"brief": brief, "items": items}


def _fallback_video_content(item: dict) -> str:
    return "\n".join(
        [
            f"0-2秒：围绕「{item['name']}」方向，用商品核心画面快速建立观看兴趣。",
            "中段：镜头保持稳定，适度推进、平移或切换细节，突出商品真实外观、适用场景和核心卖点。",
            "结尾：回到商品完整画面或使用结果，收束记忆点，保持电商短视频质感。",
            "文字/配音语言：按用户选择的最终成片语言呈现；如果选择纯音乐无口播，则不要安排口播。",
            "避免事项：不要改变商品颜色、材质、结构，不要虚构品牌、价格、认证或无法确认的信息。",
        ]
    )


def _normalize_video_strategy_response(parsed: dict, selected_item: dict) -> dict:
    raw_items = parsed.get("items")
    if not isinstance(raw_items, list):
        raw_items = []
    raw = next(
        (
            item
            for item in raw_items
            if isinstance(item, dict) and item.get("id") == selected_item["id"]
        ),
        raw_items[0] if raw_items and isinstance(raw_items[0], dict) else {},
    )
    content = _stringify_content(raw.get("content"))
    item = {
        "id": selected_item["id"],
        "name": selected_item["name"],
        "content": content or _fallback_video_content(selected_item),
    }
    brief = _stringify_content(parsed.get("brief")) or f"已生成「{selected_item['name']}」视频脚本策略。"
    return {"brief": brief, "items": [item]}


async def _request_dashscope_strategy_json(*, images: list[dict], prompt: str) -> dict:
    content = build_multimodal_image_content(images)
    content.append(
        {
            "type": "text",
            "text": "\n\n".join([prompt, MULTI_IMAGE_ANALYSIS_RULE]),
        }
    )

    payload = {
        "model": DASHSCOPE_MODEL,
        "enable_thinking": False,
        "messages": [
            {
                "role": "user",
                "content": content,
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

    return _parse_json_response(content)


def _build_strategy_prompt(
    *,
    scenario: str,
    catalog: list[dict],
    platform: str = "",
    language: str = "中文",
    product_input: str = "",
    module_ids: list[str] | None = None,
    structure: list[dict] | None = None,
    scene_description: str = "",
    selected_model_name: str = "",
    scene_ids: list[str] | None = None,
    template_prompt: str | None = None,
) -> tuple[str, str, list[dict]]:
    if scenario == "product_image":
        normalized_input = product_input.strip()
        if not normalized_input:
            raise ValueError("请先填写商品卖点与要求")
        selected_modules = _selected_product_image_modules(module_ids or [], catalog)
        return (
            build_product_image_strategy_prompt(
                platform=platform,
                language=language,
                product_input=normalized_input[:4000],
                modules=selected_modules,
                template_prompt=template_prompt,
            ),
            scenario,
            selected_modules,
        )

    if scenario == "product_suite":
        normalized_input = product_input.strip()
        if not normalized_input:
            raise ValueError("请先填写商品卖点与要求")
        selected_structures = _selected_product_suite_structures(structure or [], catalog)
        return (
            build_product_suite_strategy_prompt(
                platform=platform,
                language=language,
                product_input=normalized_input[:4000],
                structures=selected_structures,
                template_prompt=template_prompt,
            ),
            scenario,
            selected_structures,
        )

    if scenario == "outfit":
        selected_scenes = _selected_outfit_scenes(scene_ids or [], catalog)
        return (
            build_outfit_strategy_prompt(
                platform=platform,
                language=language,
                scene_description=scene_description.strip()[:4000],
                selected_model_name=selected_model_name.strip(),
                scenes=selected_scenes,
                template_prompt=template_prompt,
            ),
            scenario,
            selected_scenes,
        )

    raise ValueError("不支持的策略场景")


def _normalize_strategy_result(scenario: str, parsed: dict, selected_items: list[dict]) -> dict:
    if scenario == "product_image":
        return _normalize_strategy_response(parsed, selected_items)
    if scenario == "product_suite":
        return _normalize_suite_strategy_response(parsed, selected_items)
    if scenario == "outfit":
        return _normalize_outfit_strategy_response(parsed, selected_items)
    raise ValueError("不支持的策略场景")


async def generate_image_strategy(
    *,
    scenario: str,
    catalog: list[dict],
    images: list[dict],
    platform: str = "",
    language: str = "中文",
    product_input: str = "",
    module_ids: list[str] | None = None,
    structure: list[dict] | None = None,
    scene_description: str = "",
    selected_model_name: str = "",
    scene_ids: list[str] | None = None,
    template_prompt: str | None = None,
) -> dict:
    prompt, normalized_scenario, selected_items = _build_strategy_prompt(
        scenario=scenario,
        catalog=catalog,
        platform=platform,
        language=language,
        product_input=product_input,
        module_ids=module_ids,
        structure=structure,
        scene_description=scene_description,
        selected_model_name=selected_model_name,
        scene_ids=scene_ids,
        template_prompt=template_prompt,
    )
    parsed = await _request_dashscope_strategy_json(images=images, prompt=prompt)
    return _normalize_strategy_result(normalized_scenario, parsed, selected_items)


async def generate_video_strategy(
    *,
    type_id: str,
    name: str,
    input_mode: str,
    market: str = "",
    language: str = "中文",
    duration: int = 6,
    aspect_ratio: str = "9:16",
    product_input: str = "",
    images: list[dict],
    template_prompt: str | None = None,
) -> dict:
    normalized_type_id = str(type_id or "").strip()
    if not normalized_type_id:
        raise ValueError("视频策略缺少视频方向")
    selected_item = {
        "id": normalized_type_id,
        "name": str(name or "").strip() or normalized_type_id,
    }
    prompt = build_video_strategy_prompt(
        type_id=selected_item["id"],
        name=selected_item["name"],
        input_mode=str(input_mode or "").strip(),
        market=market,
        language=language,
        duration=duration,
        aspect_ratio=aspect_ratio,
        product_input=product_input.strip()[:4000],
        template_prompt=template_prompt,
    )
    parsed = await _request_dashscope_strategy_json(images=images, prompt=prompt)
    return _normalize_video_strategy_response(parsed, selected_item)
