from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credits import (
    DEFAULT_IMAGE_CREDIT_COSTS,
    DEFAULT_VIDEO_CREDIT_COSTS,
    normalize_image_resolution,
    normalize_video_resolution,
)
from app.core.json_utils import dump_json, parse_json_or_none
from app.models import SystemSetting

SETTING_IMAGE_CREDIT_COSTS = "image_credit_costs"
SETTING_VIDEO_CREDIT_COSTS = "video_credit_costs"
SETTING_DIGITAL_HUMAN_PRECHARGE_COSTS = "digital_human_precharge_costs"
SETTING_RECHARGE_PACKAGES = "credit_recharge_packages"

DEFAULT_DIGITAL_HUMAN_PRECHARGE_COSTS = {
    "standard": 2000,
    "premium": 5000,
}

DEFAULT_RECHARGE_PACKAGES: list[dict[str, Any]] = [
    {
        "id": "p_1000",
        "name": "1000 积分",
        "credits": 1000,
        "amount_cents": 3500,
        "badge": "",
        "enabled": True,
    },
    {
        "id": "p_2000",
        "name": "2000 积分",
        "credits": 2000,
        "amount_cents": 7000,
        "badge": "",
        "enabled": True,
    },
    {
        "id": "p_4000",
        "name": "4000 积分",
        "credits": 4000,
        "amount_cents": 14000,
        "badge": "",
        "enabled": True,
    },
    {
        "id": "p_10000",
        "name": "10000 积分",
        "credits": 10000,
        "amount_cents": 35000,
        "badge": "",
        "enabled": True,
    },
    {
        "id": "p_20000",
        "name": "20000 积分",
        "credits": 20000,
        "amount_cents": 70000,
        "badge": "",
        "enabled": True,
    },
    {
        "id": "p_40000",
        "name": "40000 积分",
        "credits": 40000,
        "amount_cents": 140000,
        "badge": "",
        "enabled": True,
    },
    {
        "id": "p_100000",
        "name": "100000 积分",
        "credits": 100000,
        "amount_cents": 350000,
        "badge": "",
        "enabled": True,
    },
    {
        "id": "p_200000",
        "name": "200000 积分",
        "credits": 200000,
        "amount_cents": 700000,
        "badge": "",
        "enabled": True,
    },
    {
        "id": "p_2000000",
        "name": "2000000 积分",
        "credits": 2000000,
        "amount_cents": 7000000,
        "badge": "",
        "enabled": True,
    },
]


def normalize_image_credit_costs(raw: dict[str, Any]) -> dict[str, int]:
    costs: dict[str, int] = {}
    for resolution in DEFAULT_IMAGE_CREDIT_COSTS:
        value = raw.get(resolution)
        if value is None:
            value = raw.get(resolution.lower())
        try:
            cost = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{resolution} 扣费必须是正整数") from exc
        if cost < 1:
            raise ValueError(f"{resolution} 扣费必须大于等于 1")
        costs[resolution] = cost
    return costs


def normalize_video_credit_costs(raw: dict[str, Any]) -> dict[str, int]:
    costs: dict[str, int] = {}
    for resolution in DEFAULT_VIDEO_CREDIT_COSTS:
        value = raw.get(resolution)
        if value is None:
            value = raw.get(resolution.upper())
        try:
            cost = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{resolution} 每秒扣费必须是正整数") from exc
        if cost < 1:
            raise ValueError(f"{resolution} 每秒扣费必须大于等于 1")
        costs[resolution] = cost
    return costs


def normalize_recharge_package(raw: dict[str, Any]) -> dict[str, Any]:
    package_id = str(raw.get("id") or "").strip()
    name = str(raw.get("name") or "").strip()
    credits = int(raw.get("credits") or 0)
    amount_cents = int(raw.get("amount_cents") or 0)
    enabled = bool(raw.get("enabled", True))
    badge = str(raw.get("badge") or "").strip()
    if not package_id:
        raise ValueError("充值套餐缺少 id")
    if not name:
        raise ValueError(f"充值套餐 {package_id} 缺少 name")
    if credits < 1:
        raise ValueError(f"充值套餐 {package_id} credits 必须大于 0")
    if amount_cents < 1:
        raise ValueError(f"充值套餐 {package_id} amount_cents 必须大于 0")
    return {
        "id": package_id,
        "name": name,
        "credits": credits,
        "amount_cents": amount_cents,
        "badge": badge,
        "enabled": enabled,
    }


def normalize_recharge_packages(
    raw: list[dict[str, Any]],
    include_disabled: bool = True,
) -> list[dict[str, Any]]:
    packages = [normalize_recharge_package(item) for item in raw if isinstance(item, dict)]
    ids = [item["id"] for item in packages]
    if len(ids) != len(set(ids)):
        raise ValueError("充值套餐 id 不能重复")
    if include_disabled:
        return packages
    return [item for item in packages if item["enabled"]]


def normalize_digital_human_precharge_costs(raw: dict[str, Any]) -> dict[str, int]:
    costs: dict[str, int] = {}
    for tier in DEFAULT_DIGITAL_HUMAN_PRECHARGE_COSTS:
        value = raw.get(tier)
        try:
            cost = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{tier} 预扣费必须是正整数") from exc
        if cost < 1:
            raise ValueError(f"{tier} 预扣费必须大于等于 1")
        costs[tier] = cost
    return costs


async def get_setting(db: AsyncSession, key: str) -> SystemSetting | None:
    return await db.get(SystemSetting, key)


async def get_effective_image_credit_costs(db: AsyncSession) -> dict[str, int]:
    setting = await get_setting(db, SETTING_IMAGE_CREDIT_COSTS)
    if setting:
        parsed = parse_json_or_none(setting.value_json)
        if not isinstance(parsed, dict):
            raise ValueError("数据库中的生图扣费配置不是有效对象")
        return normalize_image_credit_costs(parsed)
    return normalize_image_credit_costs(DEFAULT_IMAGE_CREDIT_COSTS)


async def get_effective_image_credit_cost(db: AsyncSession, resolution: str | None) -> int:
    normalized = normalize_image_resolution(resolution)
    costs = await get_effective_image_credit_costs(db)
    if normalized not in costs:
        supported = " / ".join(DEFAULT_IMAGE_CREDIT_COSTS.keys())
        raise ValueError(f"不支持的清晰度：{resolution}，请选择 {supported}")
    return costs[normalized]


async def get_effective_video_credit_costs(db: AsyncSession) -> dict[str, int]:
    setting = await get_setting(db, SETTING_VIDEO_CREDIT_COSTS)
    if setting:
        parsed = parse_json_or_none(setting.value_json)
        if not isinstance(parsed, dict):
            raise ValueError("数据库中的视频扣费配置不是有效对象")
        return normalize_video_credit_costs(parsed)
    return normalize_video_credit_costs(DEFAULT_VIDEO_CREDIT_COSTS)


async def get_effective_video_credit_cost(
    db: AsyncSession,
    resolution: str | None,
    duration: int,
) -> int:
    normalized = normalize_video_resolution(resolution)
    costs = await get_effective_video_credit_costs(db)
    if normalized not in costs:
        supported = " / ".join(DEFAULT_VIDEO_CREDIT_COSTS.keys())
        raise ValueError(f"不支持的视频清晰度：{resolution}，请选择 {supported}")
    if duration < 3 or duration > 15:
        raise ValueError("视频时长必须在 3-15 秒之间")
    return int(costs[normalized]) * int(duration)


async def get_effective_digital_human_precharge_costs(db: AsyncSession) -> dict[str, int]:
    setting = await get_setting(db, SETTING_DIGITAL_HUMAN_PRECHARGE_COSTS)
    if setting:
        parsed = parse_json_or_none(setting.value_json)
        if not isinstance(parsed, dict):
            raise ValueError("数据库中的数字人预扣费配置不是有效对象")
        return normalize_digital_human_precharge_costs(parsed)
    return normalize_digital_human_precharge_costs(DEFAULT_DIGITAL_HUMAN_PRECHARGE_COSTS)


async def get_effective_digital_human_precharge_cost(
    db: AsyncSession,
    quality_tier: str | None,
) -> int:
    costs = await get_effective_digital_human_precharge_costs(db)
    normalized = str(quality_tier or "standard").strip() or "standard"
    if normalized not in costs:
        supported = " / ".join(DEFAULT_DIGITAL_HUMAN_PRECHARGE_COSTS.keys())
        raise ValueError(f"不支持的数字人档位：{quality_tier}，请选择 {supported}")
    return int(costs[normalized])


async def get_effective_recharge_packages(
    db: AsyncSession,
    include_disabled: bool = False,
) -> list[dict[str, Any]]:
    setting = await get_setting(db, SETTING_RECHARGE_PACKAGES)
    if setting:
        parsed = parse_json_or_none(setting.value_json)
        if not isinstance(parsed, list):
            raise ValueError("数据库中的充值套餐配置不是有效数组")
        return normalize_recharge_packages(parsed, include_disabled=include_disabled)
    return normalize_recharge_packages(
        DEFAULT_RECHARGE_PACKAGES,
        include_disabled=include_disabled,
    )


async def upsert_setting(
    db: AsyncSession,
    key: str,
    value: Any,
    actor_user_id: int,
    description: str | None = None,
) -> SystemSetting:
    row = await get_setting(db, key)
    if not row:
        row = SystemSetting(key=key, value_json=dump_json(value))
    row.value_json = dump_json(value)
    row.description = description
    row.updated_by_user_id = actor_user_id
    db.add(row)
    return row


async def seed_default_billing_settings(
    db: AsyncSession,
    *,
    overwrite: bool = False,
    actor_user_id: int | None = None,
) -> dict[str, str]:
    entries = [
        (
            SETTING_IMAGE_CREDIT_COSTS,
            normalize_image_credit_costs(DEFAULT_IMAGE_CREDIT_COSTS),
            "生图分辨率扣费配置",
        ),
        (
            SETTING_VIDEO_CREDIT_COSTS,
            normalize_video_credit_costs(DEFAULT_VIDEO_CREDIT_COSTS),
            "商品视频每秒扣费配置",
        ),
        (
            SETTING_DIGITAL_HUMAN_PRECHARGE_COSTS,
            normalize_digital_human_precharge_costs(DEFAULT_DIGITAL_HUMAN_PRECHARGE_COSTS),
            "数字人预扣费配置",
        ),
        (
            SETTING_RECHARGE_PACKAGES,
            normalize_recharge_packages(DEFAULT_RECHARGE_PACKAGES, include_disabled=True),
            "积分充值套餐配置",
        ),
    ]
    results: dict[str, str] = {}
    for key, value, description in entries:
        row = await get_setting(db, key)
        if row is None:
            row = SystemSetting(key=key, value_json=dump_json(value))
            results[key] = "inserted"
        elif overwrite:
            row.value_json = dump_json(value)
            results[key] = "updated"
        else:
            results[key] = "skipped"
            continue

        row.description = description
        row.updated_by_user_id = actor_user_id
        db.add(row)
    return results
