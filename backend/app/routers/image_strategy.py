from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.image_strategy_generation import generate_image_strategy
from app.core.product_catalog import get_catalog
from app.core.prompt_template_builder import (
    build_ai_write_prompt,
    build_strategy_template_prompt,
)
from app.core.strategy.dashscope_client import (
    DashScopeConfigError,
    analyze_product_image,
    optimize_free_image_prompt,
)
from app.models import User
from app.schemas.response import Response, fail, success

router = APIRouter()


class ImageLabelItem(BaseModel):
    url: str
    label: str = ""


class AnalyzeImageRequest(BaseModel):
    images: list[ImageLabelItem]
    platform: str = ""
    scenario: str | None = None
    type_id: str | None = None


class StrategyRequest(BaseModel):
    scenario: str
    images: list[ImageLabelItem]
    platform: str = ""
    language: str = "中文"
    product_input: str = ""
    module_ids: list[str] = Field(default_factory=list)
    structure: list[dict] = Field(default_factory=list)
    scene_description: str = ""
    selected_model_name: str = ""
    scene_ids: list[str] = Field(default_factory=list)


class FreeImageOptimizeRequest(BaseModel):
    prompt: str


@router.post("/analyze", response_model=Response)
async def analyze_image(
    req: AnalyzeImageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        template_prompt = await build_ai_write_prompt(
            db,
            scenario=req.scenario or "product_suite",
            platform=req.platform,
            type_id=req.type_id,
        )
        content = await analyze_product_image(
            images=[item.model_dump() for item in req.images],
            platform=req.platform,
            prompt=template_prompt or None,
        )
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        return fail("图片分析失败")

    return success({"content": content})


@router.post("/strategy", response_model=Response)
async def image_strategy(
    req: StrategyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scenario = req.scenario.strip()
    if scenario not in {"product_image", "product_suite", "outfit"}:
        return fail("不支持的策略场景")

    try:
        template_prompt = await build_strategy_template_prompt(
            db,
            scenario=scenario,
            platform=req.platform,
        )
        catalog = await get_catalog(db, scenario=scenario)
        images = [item.model_dump() for item in req.images]
        strategy = await generate_image_strategy(
            scenario=scenario,
            catalog=catalog,
            images=images,
            platform=req.platform,
            language=req.language,
            product_input=req.product_input,
            module_ids=req.module_ids,
            structure=req.structure,
            scene_description=req.scene_description,
            selected_model_name=req.selected_model_name,
            scene_ids=req.scene_ids,
            template_prompt=template_prompt,
        )
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        messages = {
            "product_image": "详情页策略生成失败",
            "product_suite": "套图策略生成失败",
            "outfit": "穿搭策略生成失败",
        }
        return fail(messages[scenario])

    return success(strategy)


@router.post("/free-image/optimize", response_model=Response)
async def free_image_optimize(
    req: FreeImageOptimizeRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        content = await optimize_free_image_prompt(req.prompt)
    except (ValueError, DashScopeConfigError, RuntimeError) as e:
        return fail(str(e))
    except Exception:
        return fail("提示词优化失败")

    return success({"prompt": content})
