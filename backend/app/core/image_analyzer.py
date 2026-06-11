import os

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


def build_product_prompt(platform: str, language: str) -> str:
    return f"""你是电商商品图分析助手。
请根据图片内容，识别商品类型、外观、材质、用途、适用人群、核心卖点和可用于商品主图生成的关键信息。

当前投放平台：{platform or '未指定'}
输出语言：{language or '中文'}

请严格按以下格式输出，不要输出 markdown，不要输出解释，不要输出多余标题。
如果图片中无法确定某项，请基于商品外观做谨慎推测，不要编造具体品牌、认证、型号或无法从图片判断的参数。

1.产品名称：
2.核心卖点：
3.适用人群：
4.期望场景：
5.具体参数："""


async def analyze_product_image(
    *,
    image_url: str,
    platform: str = "",
    language: str = "中文",
) -> str:
    if not image_url.startswith(("http://", "https://")):
        raise ValueError("image_url必须是可访问的HTTP地址")

    payload = {
        "model": DASHSCOPE_MODEL,
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
                        "text": build_product_prompt(platform, language),
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