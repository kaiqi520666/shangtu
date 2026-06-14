from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.oss import OssConfigError, upload_image_bytes
from app.core.time import to_utc_iso, utc_now
from app.models import OutfitModel, User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/outfit", tags=["服饰穿搭"])


@router.get("/models", response_model=Response)
async def list_outfit_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_first = case((OutfitModel.user_id == current_user.id, 0), else_=1)
    user_created_at = case(
        (OutfitModel.user_id == current_user.id, OutfitModel.created_at),
        else_=None,
    )
    system_sort_order = case(
        (OutfitModel.user_id == None, OutfitModel.sort_order),  # noqa: E711
        else_=None,
    )
    system_created_at = case(
        (OutfitModel.user_id == None, OutfitModel.created_at),  # noqa: E711
        else_=None,
    )
    result = await db.execute(
        select(OutfitModel)
        .where(
            OutfitModel.active == True,  # noqa: E712
            (OutfitModel.user_id == None) | (OutfitModel.user_id == current_user.id),  # noqa: E711
        )
        .order_by(
            user_first.asc(),
            user_created_at.desc(),
            system_sort_order.asc(),
            system_created_at.asc(),
        )
    )
    items = [
        {
            "id": model.id,
            "name": model.name,
            "image_url": model.image_url,
            "object_key": model.object_key,
            "sort_order": model.sort_order,
            "is_system": model.user_id is None,
            "can_delete": model.user_id == current_user.id,
            "created_at": to_utc_iso(model.created_at),
        }
        for model in result.scalars().all()
    ]
    return success(items)


@router.post("/models/upload", response_model=Response)
async def upload_outfit_model(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        content = await file.read()
        uploaded = await upload_image_bytes(
            user_id=current_user.id,
            content=content,
            content_type=file.content_type or "",
            source="outfit-models",
        )
    except (ValueError, OssConfigError) as e:
        return fail(str(e))
    except Exception:
        return fail("模特上传失败")
    finally:
        await file.close()

    model = OutfitModel(
        name=(file.filename or "我的模特").rsplit(".", 1)[0][:100] or "我的模特",
        user_id=current_user.id,
        image_url=uploaded.url,
        object_key=uploaded.object_key,
        sort_order=0,
        active=True,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)

    return success(
        {
            "id": model.id,
            "name": model.name,
            "image_url": model.image_url,
            "object_key": model.object_key,
            "sort_order": model.sort_order,
            "is_system": False,
            "can_delete": True,
            "created_at": to_utc_iso(model.created_at),
        }
    )


@router.delete("/models/{model_id}", response_model=Response)
async def delete_outfit_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OutfitModel).where(
            OutfitModel.id == model_id,
            OutfitModel.active == True,  # noqa: E712
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        return fail("模特不存在")
    if model.user_id != current_user.id:
        return fail("只能删除自己上传的模特")

    model.active = False
    model.updated_at = utc_now()
    await db.commit()
    return success({"id": model_id})
