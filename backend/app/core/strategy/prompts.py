import json


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
请结合用户上传的视频素材图、用户选择的视频方向和补充要求，生成一条可编辑的商品视频提示词。

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
4. content 是给用户编辑并直接发送给视频模型的最终提示词，必须按 {duration} 秒时长规划镜头节奏，建议拆成 2-4 个时间段（如 0-2 秒、2-4 秒、4-{duration} 秒）。
5. content 里要明确写出：成片如需出现文字或配音，必须使用“{language or '中文'}”；如果用户选择纯音乐无口播，则不要安排口播，只保留画面文字或无文字镜头。
6. content 要覆盖开场、镜头运动、卖点呈现、画面风格和避免事项，但不要拆成多个 JSON 字段。
7. 不要编造品牌 Logo、认证、价格、销量、型号、具体参数；如果素材和补充要求中没有明确依据，只做谨慎表达。
8. 提示词要适合电商短视频，节奏清晰，主体稳定，商品外观一致，避免无意义镜头和过度夸张表达。

JSON 格式：
{{
  "brief": "一句话概括本次视频提示词方向",
  "items": [
    {{
      "id": "{type_id}",
      "name": "{name or type_id}",
      "content": "0-2秒：...\\n2-4秒：...\\n4-{duration}秒：...\\n文字/配音语言：...\\n避免事项：..."
    }}
  ]
}}"""
