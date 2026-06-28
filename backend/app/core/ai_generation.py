from app.core.strategy.catalog_select import (
    _selected_outfit_scenes,
    _selected_product_image_modules,
    _selected_product_suite_structures,
)
from app.core.strategy.dashscope_client import (
    DashScopeConfigError,
    _request_dashscope_strategy_json,
    analyze_product_image,
    optimize_free_image_prompt,
)
from app.core.strategy.parsing import (
    _normalize_outfit_strategy_response,
    _normalize_strategy_response,
    _normalize_suite_strategy_response,
)
from app.core.strategy.prompts import (
    build_outfit_strategy_prompt,
    build_product_image_strategy_prompt,
    build_product_suite_strategy_prompt,
)


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
