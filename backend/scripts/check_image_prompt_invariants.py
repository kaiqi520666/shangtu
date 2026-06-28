"""轻量回归断言：锁定"策略优先 + 生图提示词单源"这次清理的成果。

不连数据库、不调模型：monkeypatch 掉 get_prompt_templates，模拟"清理后的库"
（只在按 type_id=None 查询时返回系统/场景规则；若有人退回按真实 type_id 查询，
则模拟库会返回 per-type 行，从而被断言抓住）。

跑法：cd backend && uv run python scripts/check_image_prompt_invariants.py
任一断言失败时退出码非 0。
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core import generation_prompt_builder  # noqa: E402
from app.core.generation_prompt_builder import (  # noqa: E402
    IMAGE_GENERATE_MODEL,
    QWEN_TEXT_MODEL,
    build_image_generate_prompt,
    build_strategy_template_prompt,
    build_video_generate_prompt,
)
from app.core.prompt_templates import PromptTemplateLookupResult  # noqa: E402


SYSTEM_RULE_MARK = "【系统规则·主体一致】"
SCENE_RULE_MARK = "【场景规则】"
PER_TYPE_LEAK_MARK = "【不应出现·旧的per-type默认提示词】"
VIDEO_STRATEGY_RULE_MARK = "【视频方向规则·产品口播】"

SCENARIOS = {
    "product_image": {
        "type_id": "first-screen",
        "title": "首屏主视觉",
        "settings": {"platform": "通用", "language": "中文", "ratio": "3:4"},
    },
    "product_suite": {
        "type_id": "white-bg",
        "title": "白底图",
        "settings": {"platform": "通用", "language": "中文", "ratio": "1:1"},
    },
    "outfit": {
        "type_id": "studio",
        "title": "纯色棚拍",
        "settings": {
            "platform": "通用",
            "language": "中文",
            "ratio": "3:4",
            "sceneDescription": "干净棚拍",
            "selectedModelName": "模特A",
        },
    },
}


def _fake_template(**kwargs) -> SimpleNamespace:
    base = dict(
        id="fake",
        name="fake",
        scenario=None,
        purpose="image_generate",
        platform=None,
        type_id=None,
        model=IMAGE_GENERATE_MODEL,
        version=1,
        content="",
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def _install_fake_lookup() -> list[dict]:
    """装上模拟库的查询；返回一个列表记录每次查询的入参，供断言检查。"""
    captured: list[dict] = []

    async def fake_get_prompt_templates(db, *, scenario, purpose, platform, type_id, model):
        captured.append(
            dict(scenario=scenario, purpose=purpose, platform=platform, type_id=type_id, model=model)
        )
        templates = [
            _fake_template(id="sys-global", name="生图通用主体一致规则", content=SYSTEM_RULE_MARK),
            _fake_template(
                id=f"scene-{scenario}", name=f"{scenario}-生图场景规则", scenario=scenario,
                content=SCENE_RULE_MARK,
            ),
        ]
        if scenario == "product_video" and purpose == "strategy":
            templates = [
                _fake_template(
                    id="video-global",
                    name="商品视频-提示词生成规则",
                    scenario="product_video",
                    purpose="strategy",
                    model=QWEN_TEXT_MODEL,
                    content="【视频通用规则】",
                )
            ]
            if type_id == "product_talk":
                templates.append(
                    _fake_template(
                        id="video-product-talk",
                        name="商品视频-产品口播提示词规则",
                        scenario="product_video",
                        purpose="strategy",
                        type_id="product_talk",
                        model=QWEN_TEXT_MODEL,
                        content=VIDEO_STRATEGY_RULE_MARK,
                    )
                )
            content = "\n\n".join(t.content for t in templates if t.content)
            return PromptTemplateLookupResult(templates=templates, content=content)
        # 忠实模拟 SQL：只有按真实 type_id 查询时，库才会返回 per-type 行。
        # 当前实现应固定传 type_id=None，所以这一段永远不该触发。
        if type_id is not None:
            templates.append(
                _fake_template(
                    id=f"pertype-{type_id}", name=f"{scenario}-{type_id}默认用户提示词",
                    scenario=scenario, purpose=purpose, type_id=type_id, model=model,
                    content=PER_TYPE_LEAK_MARK,
                )
            )
        content = "\n\n".join(t.content for t in templates if t.content)
        return PromptTemplateLookupResult(templates=templates, content=content)

    generation_prompt_builder.get_prompt_templates = fake_get_prompt_templates
    return captured


def _fake_job(scenario: str, settings: dict) -> SimpleNamespace:
    return SimpleNamespace(
        scenario=scenario,
        input_text="测试商品卖点：轻便、耐用、适合日常。",
        settings_json=json.dumps(settings, ensure_ascii=False),
    )


class CheckFailed(Exception):
    pass


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise CheckFailed(msg)


async def _check_scenario(scenario: str, cfg: dict, captured: list[dict]) -> None:
    strategy_content = f"【策略内容·{scenario}】模特/构图/卖点表达由 qwen 策略提供。"
    job = _fake_job(scenario, cfg["settings"])

    captured.clear()
    result = await build_image_generate_prompt(
        db=None,
        job=job,
        type_id=cfg["type_id"],
        title=cfg["title"],
        user_prompt=strategy_content,
    )

    snapshot = result.prompt_snapshot
    refs = snapshot["template_refs"]

    # 不变式 ①：查询固定 type_id=None（防止重新去拉 per-type 默认模板）
    require(len(captured) == 1, f"[{scenario}] 期望恰好一次模板查询，实得 {len(captured)}")
    require(captured[0]["type_id"] is None, f"[{scenario}] 生图查询必须 type_id=None，实得 {captured[0]['type_id']!r}")
    require(
        captured[0]["purpose"] == "image_generate" and captured[0]["model"] == IMAGE_GENERATE_MODEL,
        f"[{scenario}] 查询的 purpose/model 不对：{captured[0]}",
    )

    # 不变式 ②：最终 prompt / refs 不得混入任何 per-type 默认提示词
    require(PER_TYPE_LEAK_MARK not in result.final_prompt, f"[{scenario}] 最终 prompt 混入了 per-type 默认提示词")
    require(all(r["type_id"] is None for r in refs), f"[{scenario}] template_refs 出现了 type_id：{refs}")

    # 不变式 ③：画面要求只来自策略内容，且系统规则在场
    require(strategy_content in result.final_prompt, f"[{scenario}] 策略内容未进入最终 prompt")
    require(snapshot["user"] == strategy_content, f"[{scenario}] snapshot.user 应等于策略内容")
    require(SYSTEM_RULE_MARK in result.final_prompt, f"[{scenario}] 系统规则缺失")

    print(f"  ✓ {scenario}: type_id=None / 无 per-type 泄漏 / 策略内容贯通")


async def _check_video_strategy_lookup(captured: list[dict]) -> None:
    captured.clear()
    content = await build_strategy_template_prompt(
        db=None,
        scenario="product_video",
        platform="global",
        type_id="product_talk",
    )
    require(len(captured) == 1, f"[product_video] 期望恰好一次策略模板查询，实得 {len(captured)}")
    require(captured[0]["purpose"] == "strategy", f"[product_video] 查询 purpose 不对：{captured[0]}")
    require(captured[0]["type_id"] == "product_talk", f"[product_video] 策略查询必须传视频方向 type_id：{captured[0]}")
    require(VIDEO_STRATEGY_RULE_MARK in content, "[product_video] 策略模板缺少当前视频方向规则")
    print("  ✓ product_video strategy: 查询通用规则 + 当前方向规则")


async def _check_empty_user_prompt_rejected() -> None:
    cfg = SCENARIOS["product_image"]
    job = _fake_job("product_image", cfg["settings"])
    try:
        await build_image_generate_prompt(
            db=None, job=job, type_id=cfg["type_id"], title=cfg["title"], user_prompt="   ",
        )
    except ValueError as exc:
        require("请先生成并确认图片策略" in str(exc), f"空策略报错文案不符：{exc}")
        print("  ✓ 空 user_prompt 被拒：'请先生成并确认图片策略'")
        return
    raise CheckFailed("空 user_prompt 未被拒绝（策略内容应为必填）")


async def _check_video(captured: list[dict]) -> None:
    prompt_content = "【视频提示词】开场展示商品核心画面，镜头推进到细节，最后呈现使用场景。"
    settings = {
        "platform": "global",
        "language": "english",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "duration": 6,
        "input_mode": "image_to_video",
    }

    captured.clear()
    result = await build_video_generate_prompt(
        db=None,
        type_id="ugc_seeding",
        title="UGC种草",
        user_prompt=prompt_content,
        settings=settings,
    )

    snapshot = result.prompt_snapshot
    require(len(captured) == 0, f"[product_video] 不应查询隐藏生成模板，实得 {len(captured)} 次")
    require(PER_TYPE_LEAK_MARK not in result.final_prompt, "[product_video] 最终 prompt 混入了 per-type 默认提示词")
    require(result.final_prompt == prompt_content, "[product_video] final prompt 应等于用户确认的视频提示词")
    require(snapshot["system"] == "", "[product_video] snapshot.system 应为空")
    require(snapshot["task"] == "", "[product_video] snapshot.task 应为空")
    require(snapshot["user"] == prompt_content, "[product_video] snapshot.user 应等于视频提示词")
    require(snapshot["template_refs"] == [], "[product_video] 不应记录隐藏生成模板 refs")

    try:
        await build_video_generate_prompt(
            db=None,
            type_id="ugc_seeding",
            title="UGC种草",
            user_prompt=" ",
            settings=settings,
        )
    except ValueError as exc:
        require("请先生成并确认视频提示词" in str(exc), f"视频空提示词报错文案不符：{exc}")
        print("  ✓ product_video: 零隐藏模板 / final 等于可见提示词 / 视频提示词必填")
        return
    raise CheckFailed("视频空 user_prompt 未被拒绝（视频提示词内容应为必填）")


async def main() -> None:
    captured = _install_fake_lookup()
    print("生图提示词单源回归断言：")
    for scenario, cfg in SCENARIOS.items():
        await _check_scenario(scenario, cfg, captured)
    await _check_video_strategy_lookup(captured)
    await _check_empty_user_prompt_rejected()
    await _check_video(captured)
    print("ALL PASS")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except CheckFailed as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
