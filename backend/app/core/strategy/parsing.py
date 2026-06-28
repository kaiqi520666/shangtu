import json
import re


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
    brief = _stringify_content(parsed.get("brief")) or f"已生成「{selected_item['name']}」视频提示词。"
    return {"brief": brief, "items": [item]}
