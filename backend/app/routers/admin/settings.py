from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_env
from app.core.deps import get_current_super_admin, get_db
from app.core.system_settings import (
    SETTING_DIGITAL_HUMAN_CREDIT_COSTS,
    SETTING_DIGITAL_HUMAN_PRECHARGE_COSTS,
    SETTING_IMAGE_CREDIT_COSTS,
    SETTING_RECHARGE_PACKAGES,
    SETTING_VIDEO_TRANSLATION_CREDIT_COSTS,
    SETTING_VIDEO_CREDIT_COSTS,
    SETTING_VOICEOVER_CREDIT_COST,
    get_effective_digital_human_credit_costs,
    get_effective_digital_human_precharge_costs,
    normalize_digital_human_credit_costs,
    normalize_digital_human_precharge_costs,
    get_effective_image_credit_costs,
    get_effective_recharge_packages,
    get_effective_video_translation_credit_costs,
    get_effective_video_credit_costs,
    get_effective_voiceover_credit_cost,
    normalize_image_credit_costs,
    normalize_recharge_packages,
    normalize_video_translation_credit_costs,
    normalize_video_credit_costs,
    normalize_voiceover_credit_cost,
    upsert_setting,
)
from app.models import User
from app.schemas.response import Response, fail, success

from .schemas import AdminSettingsRequest
from .utils import audit_log

router = APIRouter()


@router.get("/settings", response_model=Response)
async def get_settings(
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        image_credit_costs = await get_effective_image_credit_costs(db)
        video_credit_costs = await get_effective_video_credit_costs(db)
        digital_human_credit_costs = await get_effective_digital_human_credit_costs(db)
        digital_human_precharge_costs = await get_effective_digital_human_precharge_costs(db)
        video_translation_credit_costs = await get_effective_video_translation_credit_costs(db)
        voiceover_credit_cost = await get_effective_voiceover_credit_cost(db)
        recharge_packages = await get_effective_recharge_packages(db, include_disabled=True)
    except ValueError as exc:
        return fail(str(exc))
    payment_config = {
        "zpay_pid_configured": bool(get_env("ZPAY_PID")),
        "zpay_key_configured": bool(get_env("ZPAY_KEY")),
        "zpay_notify_url_configured": bool(get_env("ZPAY_NOTIFY_URL")),
        "zpay_return_url_configured": bool(get_env("ZPAY_RETURN_URL")),
    }
    return success(
        {
            "image_credit_costs": image_credit_costs,
            "video_credit_costs": video_credit_costs,
            "digital_human_credit_costs": digital_human_credit_costs,
            "digital_human_precharge_costs": digital_human_precharge_costs,
            "video_translation_credit_costs": video_translation_credit_costs,
            "voiceover_credit_cost_per_100_chars": voiceover_credit_cost,
            "recharge_packages": recharge_packages,
            "payment_config": payment_config,
        }
    )


@router.put("/settings", response_model=Response)
async def update_settings(
    req: AdminSettingsRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        image_credit_costs = normalize_image_credit_costs(req.image_credit_costs)
        video_credit_costs = normalize_video_credit_costs(req.video_credit_costs)
        digital_human_credit_costs = normalize_digital_human_credit_costs(
            req.digital_human_credit_costs
        )
        digital_human_precharge_costs = normalize_digital_human_precharge_costs(
            req.digital_human_precharge_costs
        )
        video_translation_credit_costs = normalize_video_translation_credit_costs(
            req.video_translation_credit_costs
        )
        voiceover_credit_cost = normalize_voiceover_credit_cost(
            req.voiceover_credit_cost_per_100_chars
        )
        recharge_packages = normalize_recharge_packages(
            [item.model_dump() for item in req.recharge_packages],
            include_disabled=True,
        )
    except ValueError as exc:
        return fail(str(exc))

    await upsert_setting(
        db,
        SETTING_IMAGE_CREDIT_COSTS,
        image_credit_costs,
        current_admin.id,
        "生图分辨率扣费配置",
    )
    await upsert_setting(
        db,
        SETTING_VOICEOVER_CREDIT_COST,
        voiceover_credit_cost,
        current_admin.id,
        "AI配音每100字符扣费配置",
    )
    await upsert_setting(
        db,
        SETTING_VIDEO_CREDIT_COSTS,
        video_credit_costs,
        current_admin.id,
        "商品视频每秒扣费配置",
    )
    await upsert_setting(
        db,
        SETTING_DIGITAL_HUMAN_CREDIT_COSTS,
        digital_human_credit_costs,
        current_admin.id,
        "数字人每秒扣费配置",
    )
    await upsert_setting(
        db,
        SETTING_DIGITAL_HUMAN_PRECHARGE_COSTS,
        digital_human_precharge_costs,
        current_admin.id,
        "数字人预扣费配置",
    )
    await upsert_setting(
        db,
        SETTING_VIDEO_TRANSLATION_CREDIT_COSTS,
        video_translation_credit_costs,
        current_admin.id,
        "视频翻译每秒扣费配置",
    )
    await upsert_setting(
        db,
        SETTING_RECHARGE_PACKAGES,
        recharge_packages,
        current_admin.id,
        "积分充值套餐配置",
    )
    db.add(
        audit_log(
            current_admin,
            "update_settings",
            "system_settings",
            "billing",
            {
                "image_credit_costs": image_credit_costs,
                "video_credit_costs": video_credit_costs,
                "digital_human_credit_costs": digital_human_credit_costs,
                "digital_human_precharge_costs": digital_human_precharge_costs,
                "video_translation_credit_costs": video_translation_credit_costs,
                "voiceover_credit_cost_per_100_chars": voiceover_credit_cost,
                "recharge_packages_count": len(recharge_packages),
            },
        )
    )
    await db.commit()
    return success(
        {
            "image_credit_costs": image_credit_costs,
            "video_credit_costs": video_credit_costs,
            "digital_human_credit_costs": digital_human_credit_costs,
            "digital_human_precharge_costs": digital_human_precharge_costs,
            "video_translation_credit_costs": video_translation_credit_costs,
            "voiceover_credit_cost_per_100_chars": voiceover_credit_cost,
            "recharge_packages": recharge_packages,
        }
    )
