import json
from types import SimpleNamespace

import pytest

from app.core import generation_prompt_builder, prompt_template_builder
from app.core.generation_prompt_builder import IMAGE_GENERATE_MODEL, build_image_generate_prompt
from app.core.model_config import QWEN_TEXT_MODEL
from app.core.prompt_template_builder import build_strategy_template_prompt
from app.core.prompt_templates import PromptTemplateLookupResult
from app.core.video_prompt_builder import build_video_generate_prompt

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


def fake_template(**kwargs):
    values = {
        "id": "fake",
        "name": "fake",
        "scenario": None,
        "purpose": "image_generate",
        "platform": None,
        "type_id": None,
        "model": IMAGE_GENERATE_MODEL,
        "version": 1,
        "content": "",
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


@pytest.fixture
def template_lookup(monkeypatch):
    captured = []

    async def fake_get_prompt_templates(
        db, *, scenario, purpose, platform, type_id, model
    ):
        captured.append(
            {
                "scenario": scenario,
                "purpose": purpose,
                "platform": platform,
                "type_id": type_id,
                "model": model,
            }
        )
        templates = [
            fake_template(
                id="sys-global",
                name="生图通用主体一致规则",
                content=SYSTEM_RULE_MARK,
            ),
            fake_template(
                id=f"scene-{scenario}",
                name=f"{scenario}-生图场景规则",
                scenario=scenario,
                content=SCENE_RULE_MARK,
            ),
        ]
        if scenario == "product_video" and purpose == "strategy":
            templates = [
                fake_template(
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
                    fake_template(
                        id="video-product-talk",
                        name="商品视频-产品口播提示词规则",
                        scenario="product_video",
                        purpose="strategy",
                        type_id="product_talk",
                        model=QWEN_TEXT_MODEL,
                        content=VIDEO_STRATEGY_RULE_MARK,
                    )
                )
        elif type_id is not None:
            templates.append(
                fake_template(
                    id=f"pertype-{type_id}",
                    name=f"{scenario}-{type_id}默认用户提示词",
                    scenario=scenario,
                    purpose=purpose,
                    type_id=type_id,
                    model=model,
                    content=PER_TYPE_LEAK_MARK,
                )
            )
        content = "\n\n".join(template.content for template in templates if template.content)
        return PromptTemplateLookupResult(templates=templates, content=content)

    monkeypatch.setattr(
        generation_prompt_builder,
        "get_prompt_templates",
        fake_get_prompt_templates,
    )
    monkeypatch.setattr(
        prompt_template_builder,
        "get_prompt_templates",
        fake_get_prompt_templates,
    )
    return captured


def fake_job(scenario, settings):
    return SimpleNamespace(
        scenario=scenario,
        input_text="测试商品卖点：轻便、耐用、适合日常。",
        settings_json=json.dumps(settings, ensure_ascii=False),
    )


@pytest.mark.parametrize(("scenario", "config"), SCENARIOS.items())
async def test_image_prompt_uses_strategy_and_scene_rules_without_per_type_template(
    scenario,
    config,
    template_lookup,
):
    strategy_content = f"【策略内容·{scenario}】模特/构图/卖点表达由 qwen 策略提供。"

    result = await build_image_generate_prompt(
        db=None,
        job=fake_job(scenario, config["settings"]),
        type_id=config["type_id"],
        title=config["title"],
        user_prompt=strategy_content,
    )

    assert len(template_lookup) == 1
    assert template_lookup[0]["type_id"] is None
    assert template_lookup[0]["purpose"] == "image_generate"
    assert template_lookup[0]["model"] == IMAGE_GENERATE_MODEL
    assert PER_TYPE_LEAK_MARK not in result.final_prompt
    assert all(ref["type_id"] is None for ref in result.prompt_snapshot["template_refs"])
    assert strategy_content in result.final_prompt
    assert result.prompt_snapshot["user"] == strategy_content
    assert SYSTEM_RULE_MARK in result.final_prompt


async def test_product_video_strategy_includes_selected_direction_rule(template_lookup):
    content = await build_strategy_template_prompt(
        db=None,
        scenario="product_video",
        platform="global",
        type_id="product_talk",
    )

    assert len(template_lookup) == 1
    assert template_lookup[0]["purpose"] == "strategy"
    assert template_lookup[0]["type_id"] == "product_talk"
    assert VIDEO_STRATEGY_RULE_MARK in content


async def test_image_prompt_rejects_empty_strategy(template_lookup):
    config = SCENARIOS["product_image"]

    with pytest.raises(ValueError, match="请先生成并确认图片策略"):
        await build_image_generate_prompt(
            db=None,
            job=fake_job("product_image", config["settings"]),
            type_id=config["type_id"],
            title=config["title"],
            user_prompt="   ",
        )


async def test_video_prompt_uses_confirmed_prompt_without_hidden_templates(template_lookup):
    prompt_content = "【视频提示词】开场展示商品核心画面，镜头推进到细节，最后呈现使用场景。"
    settings = {
        "platform": "global",
        "language": "english",
        "aspect_ratio": "9:16",
        "resolution": "1080p",
        "duration": 6,
        "input_mode": "image_to_video",
    }

    result = await build_video_generate_prompt(
        db=None,
        type_id="ugc_seeding",
        title="UGC种草",
        user_prompt=prompt_content,
        settings=settings,
    )

    assert template_lookup == []
    assert PER_TYPE_LEAK_MARK not in result.final_prompt
    assert result.final_prompt == prompt_content
    assert result.prompt_snapshot["system"] == ""
    assert result.prompt_snapshot["task"] == ""
    assert result.prompt_snapshot["user"] == prompt_content
    assert result.prompt_snapshot["template_refs"] == []

    with pytest.raises(ValueError, match="请先生成并确认视频提示词"):
        await build_video_generate_prompt(
            db=None,
            type_id="ugc_seeding",
            title="UGC种草",
            user_prompt=" ",
            settings=settings,
        )