from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import OutfitModel, User
from app.schemas.response import Response, success

router = APIRouter(prefix="/outfit", tags=["服饰穿搭"])


@router.get("/models", response_model=Response)
async def list_outfit_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OutfitModel)
        .where(OutfitModel.active == True)  # noqa: E712
        .order_by(OutfitModel.sort_order.asc(), OutfitModel.created_at.asc())
    )
    items = [
        {
            "id": model.id,
            "name": model.name,
            "image_url": model.image_url,
            "object_key": model.object_key,
            "sort_order": model.sort_order,
        }
        for model in result.scalars().all()
    ]
    return success(items)
