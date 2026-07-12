from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.pagination import PaginationParams, execute_pagination, page_payload, pagination_params
from app.core.time import utc_now
from app.models import ProductCatalog, User
from app.schemas.response import Response, fail, success

from .schemas import ProductCatalogRequest
from .utils import audit_log, product_catalog_payload

router = APIRouter()

VALID_CATALOG_SCENARIOS = {"product_image", "product_suite", "outfit"}


@router.get("/product-catalog", response_model=Response)
async def list_product_catalog(
    pagination: PaginationParams = Depends(pagination_params),
    scenario: str | None = None,
    enabled: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if scenario in VALID_CATALOG_SCENARIOS:
        conditions.append(ProductCatalog.scenario == scenario)
    if enabled in {"true", "false"}:
        conditions.append(ProductCatalog.enabled == (enabled == "true"))
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                ProductCatalog.item_id.ilike(like),
                ProductCatalog.name.ilike(like),
                ProductCatalog.description.ilike(like),
                ProductCatalog.strategy.ilike(like),
            )
        )

    total_stmt = select(func.count()).select_from(ProductCatalog)
    data_stmt = select(ProductCatalog).order_by(
        ProductCatalog.scenario.asc(),
        ProductCatalog.sort.asc(),
        ProductCatalog.item_id.asc(),
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)

    total, result = await execute_pagination(
        db,
        count_statement=total_stmt,
        data_statement=data_stmt,
        pagination=pagination,
    )
    items = [product_catalog_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, pagination.page, pagination.page_size))


@router.patch("/product-catalog/{catalog_id}", response_model=Response)
async def update_product_catalog(
    catalog_id: str,
    req: ProductCatalogRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProductCatalog).where(ProductCatalog.id == catalog_id))
    item = result.scalar_one_or_none()
    if not item:
        return fail("目录项不存在")

    try:
        data = _normalize_product_catalog(req, item.scenario)
    except ValueError as exc:
        return fail(str(exc))

    for key, value in data.items():
        setattr(item, key, value)
    item.updated_at = utc_now()
    db.add(
        audit_log(
            current_admin,
            "update_product_catalog",
            "product_catalog",
            item.id,
            {
                "scenario": item.scenario,
                "item_id": item.item_id,
                "name": item.name,
                "enabled": item.enabled,
                "sort": item.sort,
            },
        )
    )
    await db.commit()
    await db.refresh(item)
    return success(product_catalog_payload(item))


def _normalize_product_catalog(req: ProductCatalogRequest, scenario: str) -> dict:
    name = req.name.strip()
    description = req.description.strip()
    strategy = req.strategy.strip()
    if not name:
        raise ValueError("目录名称不能为空")
    if not description:
        raise ValueError("展示描述不能为空")
    if not strategy:
        raise ValueError("生成策略不能为空")

    default_count = req.default_count
    max_count = req.max_count
    if scenario == "product_suite":
        if default_count is None:
            raise ValueError("商品套图默认张数不能为空")
        if max_count is None:
            raise ValueError("商品套图最大张数不能为空")
        if default_count > max_count:
            raise ValueError("默认张数不能大于最大张数")
    else:
        default_count = None
        max_count = None

    return {
        "name": name,
        "description": description,
        "strategy": strategy,
        "default_count": default_count,
        "max_count": max_count,
        "enabled": req.enabled,
        "sort": req.sort,
    }
