from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.oss import OssConfigError, upload_image_bytes
from app.core.time import utc_now
from app.models import OutfitModel, User
from app.schemas.response import Response, fail, success

from .schemas import UpdateOutfitModelRequest
from .utils import audit_log, outfit_model_payload, page_payload

router = APIRouter()


@router.get("/outfit-models", response_model=Response)
async def list_system_outfit_models(
    page: int = 1,
    page_size: int = 20,
    active: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = [OutfitModel.user_id.is_(None)]
    if active in {"true", "false"}:
        conditions.append(OutfitModel.active == (active == "true"))
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                OutfitModel.name.ilike(like),
                OutfitModel.object_key.ilike(like),
                OutfitModel.image_url.ilike(like),
            )
        )

    total_stmt = select(func.count()).select_from(OutfitModel)
    data_stmt = select(OutfitModel).order_by(
        OutfitModel.sort_order.asc(),
        OutfitModel.created_at.desc(),
        OutfitModel.id.desc(),
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)

    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [outfit_model_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, page, page_size))


@router.post("/outfit-models/upload", response_model=Response)
async def upload_system_outfit_model(
    name: str | None = Form(default=None),
    sort_order: int = Form(default=0),
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        content = await file.read()
        uploaded = await upload_image_bytes(
            user_id=0,
            content=content,
            content_type=file.content_type or "",
            source="system/outfit-models",
        )
    except (ValueError, OssConfigError) as exc:
        return fail(str(exc))
    except Exception:
        return fail("系统模特上传失败")
    finally:
        await file.close()

    model_name = (name or (file.filename or "系统模特").rsplit(".", 1)[0]).strip()[:100] or "系统模特"
    model = OutfitModel(
        name=model_name,
        user_id=None,
        image_url=uploaded.url,
        object_key=uploaded.object_key,
        sort_order=sort_order,
        active=True,
    )
    db.add(model)
    await db.flush()
    db.add(
        audit_log(
            current_admin,
            "create_outfit_model",
            "outfit_model",
            model.id,
            {"name": model.name, "object_key": model.object_key, "sort_order": sort_order},
        )
    )
    await db.commit()
    await db.refresh(model)
    return success(outfit_model_payload(model))


@router.patch("/outfit-models/{model_id}", response_model=Response)
async def update_system_outfit_model(
    model_id: str,
    req: UpdateOutfitModelRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    model = await _get_system_model(db, model_id)
    if not model:
        return fail("系统模特不存在")

    if req.name is not None:
        name = req.name.strip()
        if not name:
            return fail("模特名称不能为空")
        model.name = name
    if req.sort_order is not None:
        model.sort_order = req.sort_order
    if req.active is not None:
        model.active = req.active
    model.updated_at = utc_now()
    db.add(
        audit_log(
            current_admin,
            "update_outfit_model",
            "outfit_model",
            model.id,
            {"name": model.name, "sort_order": model.sort_order, "active": model.active},
        )
    )
    await db.commit()
    await db.refresh(model)
    return success(outfit_model_payload(model))


@router.delete("/outfit-models/{model_id}", response_model=Response)
async def delete_system_outfit_model(
    model_id: str,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    model = await _get_system_model(db, model_id)
    if not model:
        return fail("系统模特不存在")

    # 物理删除 DB 记录，不删 OSS 文件。当前前端未开放此入口，统一用 PATCH active=false 停用。
    await db.delete(model)
    db.add(
        audit_log(
            current_admin,
            "delete_outfit_model",
            "outfit_model",
            model.id,
            {"name": model.name, "object_key": model.object_key},
        )
    )
    await db.commit()
    return success({"id": model.id})


async def _get_system_model(db: AsyncSession, model_id: str) -> OutfitModel | None:
    result = await db.execute(
        select(OutfitModel).where(
            OutfitModel.id == model_id,
            OutfitModel.user_id.is_(None),
        )
    )
    return result.scalar_one_or_none()
