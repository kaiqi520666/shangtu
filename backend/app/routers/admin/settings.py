import os

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.system_settings import (
    SETTING_DIGITAL_HUMAN_CREDIT_COSTS,
    SETTING_DIGITAL_HUMAN_PRECHARGE_COSTS,
    SETTING_IMAGE_CREDIT_COSTS,
    SETTING_RECHARGE_PACKAGES,
    SETTING_VIDEO_TRANSLATION_CREDIT_COSTS,
    SETTING_VIDEO_CREDIT_COSTS,
    get_effective_digital_human_credit_costs,
    get_effective_digital_human_precharge_costs,
    normalize_digital_human_credit_costs,
    normalize_digital_human_precharge_costs,
    get_effective_image_credit_costs,
    get_effective_recharge_packages,
    get_effective_video_translation_credit_costs,
    get_effective_video_credit_costs,
    normalize_image_credit_costs,
    normalize_recharge_packages,
    normalize_video_translation_credit_costs,
    normalize_video_credit_costs,
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
        recharge_packages = await get_effective_recharge_packages(db, include_disabled=True)
    except ValueError as exc:
        return fail(str(exc))
    payment_config = {
        "zpay_pid_configured": bool(os.getenv("ZPAY_PID")),
        "zpay_key_configured": bool(os.getenv("ZPAY_KEY")),
        "zpay_notify_url_configured": bool(os.getenv("ZPAY_NOTIFY_URL")),
        "zpay_return_url_configured": bool(os.getenv("ZPAY_RETURN_URL")),
    }
    return success(
        {
            "image_credit_costs": image_credit_costs,
            "video_credit_costs": video_credit_costs,
            "digital_human_credit_costs": digital_human_credit_costs,
            "digital_human_precharge_costs": digital_human_precharge_costs,
            "video_translation_credit_costs": video_translation_credit_costs,
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
            "recharge_packages": recharge_packages,
        }
    )
