from app.core.strategy.dashscope_client import _request_dashscope_strategy_json
from app.core.strategy.parsing import _normalize_video_strategy_response
from app.core.strategy.prompts import build_video_strategy_prompt


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
        raise ValueError("视频提示词缺少视频方向")
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
