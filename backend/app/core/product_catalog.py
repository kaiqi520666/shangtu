from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProductCatalog

CATALOG_SCENARIOS = ("product_image", "product_suite", "outfit")


def serialize_catalog_item(item: ProductCatalog) -> dict:
    return {
        "id": item.item_id,
        "name": item.name,
        "desc": item.description,
        "strategy": item.strategy,
        "default_count": item.default_count,
        "max_count": item.max_count,
    }


async def get_catalog(db: AsyncSession, *, scenario: str) -> list[dict]:
    scenario = scenario.strip()
    if not scenario:
        raise ValueError("目录场景不能为空")

    result = await db.execute(
        select(ProductCatalog)
        .where(
            ProductCatalog.scenario == scenario,
            ProductCatalog.enabled == True,  # noqa: E712
        )
        .order_by(ProductCatalog.sort.asc(), ProductCatalog.item_id.asc())
    )
    return [serialize_catalog_item(item) for item in result.scalars().all()]


async def get_all_catalog(db: AsyncSession) -> dict[str, list[dict]]:
    return {
        scenario: await get_catalog(db, scenario=scenario)
        for scenario in CATALOG_SCENARIOS
    }
