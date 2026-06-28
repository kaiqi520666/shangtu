PROVIDER_ERROR_COPY = {
    "image": {
        "default": "生图失败，请调整提示词后重试。",
        "unsafe": "生成内容触发平台安全策略，请尝试减少敏感词、夸张功效、品牌/认证/人物相关描述后重新生成。",
        "rate_limit": "生图服务繁忙，请稍后再试。",
        "timeout": "生图任务超时，请稍后重试。",
        "upstream": "上游生图服务暂时失败，请稍后重试。",
    },
    "video": {
        "default": "视频生成失败，请调整提示词或参考图后重试。",
        "unsafe": "视频内容触发平台安全策略，请减少敏感词、夸张功效、品牌/认证/人物相关描述后重新生成。",
        "rate_limit": "视频生成服务繁忙，请稍后再试。",
        "timeout": "视频生成任务超时，请稍后重试。",
        "upstream": "上游视频生成服务暂时失败，请稍后重试。",
    },
}

PROVIDER_ERROR_RULES = [
    ("unsafe", ("image_unsafe", "unsafe")),
    ("rate_limit", ("rate limit", "too many requests", "429")),
    ("timeout", ("timeout", "timed out")),
    ("upstream", ("upstream api failed", "upstream")),
]


def normalize_provider_error(message: str | None, media_type: str = "image") -> str:
    """把上游 / 第三方原始错误归一化为对用户友好的中文文案；技术原文交给日志。"""
    copy = PROVIDER_ERROR_COPY.get(media_type) or PROVIDER_ERROR_COPY["image"]
    if not message:
        return copy["default"]
    lower = message.lower()
    for error_type, keywords in PROVIDER_ERROR_RULES:
        if any(keyword in lower for keyword in keywords):
            return copy[error_type]
    if "超时" in message:
        return copy["timeout"]
    if any("一" <= ch <= "鿿" for ch in message):
        return message
    return copy["default"]
