from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.providers.toapis_provider import TOAPIS_SIZE_TABLE
from app.core.product_catalog import get_all_catalog
from app.core.system_settings import get_effective_image_credit_costs
from app.models import User
from app.schemas.response import Response, fail, success

router = APIRouter()


@router.get("/capabilities", response_model=Response)
async def image_capabilities():
    return success({"resolution_map": TOAPIS_SIZE_TABLE})


@router.get("/catalog", response_model=Response)
async def image_catalog(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return success(await get_all_catalog(db))


@router.get("/credit-costs", response_model=Response)
async def image_credit_costs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        costs = await get_effective_image_credit_costs(db)
    except ValueError as exc:
        return fail(str(exc))
    return success({"costs": costs, "consumption_multiplier": float(current_user.consumption_multiplier)})
