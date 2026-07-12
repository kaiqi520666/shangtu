import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.pagination import PaginationParams, execute_pagination, page_payload, pagination_params
from app.core.time import utc_now
from app.models import HeygenAvatar, HeygenVoice, User
from app.schemas.response import Response, fail, success
from app.services.heygen_resources import sync_heygen_resources
from app.core.providers.heygen_provider import HeygenConfigError

from .schemas import UpdateHeygenResourceRequest
from .utils import (
    audit_log,
    heygen_avatar_payload,
    heygen_voice_payload,
)

router = APIRouter()


@router.get("/heygen-avatars", response_model=Response)
async def list_heygen_avatars(
    pagination: PaginationParams = Depends(pagination_params),
    active: str | None = None,
    gender: str | None = None,
    orientation: str | None = None,
    engine: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if active in {"true", "false"}:
        conditions.append(HeygenAvatar.enabled == (active == "true"))
    if gender in {"male", "female"}:
        conditions.append(func.lower(HeygenAvatar.gender) == gender)
    if orientation in {"portrait", "landscape"}:
        conditions.append(HeygenAvatar.preferred_orientation == orientation)
    if engine in {"avatar_iii", "avatar_iv", "avatar_v"}:
        conditions.append(HeygenAvatar.supported_api_engines_json.ilike(f'%"{engine}"%'))
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                HeygenAvatar.name.ilike(like),
                HeygenAvatar.avatar_id.ilike(like),
                HeygenAvatar.group_id.ilike(like),
                HeygenAvatar.default_voice_id.ilike(like),
            )
        )

    total_stmt = select(func.count()).select_from(HeygenAvatar)
    data_stmt = select(HeygenAvatar).order_by(
        HeygenAvatar.sort_order.asc(),
        HeygenAvatar.updated_at.desc(),
        HeygenAvatar.id.desc(),
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
    items = [heygen_avatar_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, pagination.page, pagination.page_size))


@router.patch("/heygen-avatars/{avatar_row_id}", response_model=Response)
async def update_heygen_avatar(
    avatar_row_id: str,
    req: UpdateHeygenResourceRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_heygen_avatar(db, avatar_row_id)
    if not item:
        return fail("系统数字人不存在")

    if req.name is not None:
        name = req.name.strip()
        if not name:
            return fail("数字人名称不能为空")
        item.name = name
    if req.sort_order is not None:
        item.sort_order = req.sort_order
    if req.enabled is not None:
        item.enabled = req.enabled
    item.updated_at = utc_now()
    db.add(
        audit_log(
            current_admin,
            "update_heygen_avatar",
            "heygen_avatar",
            item.id,
            {
                "avatar_id": item.avatar_id,
                "name": item.name,
                "enabled": item.enabled,
                "sort_order": item.sort_order,
            },
        )
    )
    await db.commit()
    await db.refresh(item)
    return success(heygen_avatar_payload(item))


@router.get("/heygen-voices", response_model=Response)
async def list_heygen_voices(
    pagination: PaginationParams = Depends(pagination_params),
    active: str | None = None,
    gender: str | None = None,
    language: str | None = None,
    support_locale: str | None = None,
    support_pause: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if active in {"true", "false"}:
        conditions.append(HeygenVoice.enabled == (active == "true"))
    if gender in {"male", "female", "unknown"}:
        conditions.append(func.lower(HeygenVoice.gender) == gender)
    if language:
        if language == "__multilingual__":
            conditions.append(HeygenVoice.language == "Multilingual")
        else:
            conditions.append(HeygenVoice.language == language)
    if support_locale in {"true", "false"}:
        conditions.append(HeygenVoice.support_locale == (support_locale == "true"))
    if support_pause in {"true", "false"}:
        conditions.append(HeygenVoice.support_pause == (support_pause == "true"))
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                HeygenVoice.name.ilike(like),
                HeygenVoice.voice_id.ilike(like),
                HeygenVoice.language.ilike(like),
            )
        )

    total_stmt = select(func.count()).select_from(HeygenVoice)
    data_stmt = select(HeygenVoice).order_by(
        HeygenVoice.sort_order.asc(),
        HeygenVoice.updated_at.desc(),
        HeygenVoice.id.desc(),
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
    items = [heygen_voice_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, pagination.page, pagination.page_size))


@router.patch("/heygen-voices/{voice_row_id}", response_model=Response)
async def update_heygen_voice(
    voice_row_id: str,
    req: UpdateHeygenResourceRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_heygen_voice(db, voice_row_id)
    if not item:
        return fail("系统声音不存在")

    if req.name is not None:
        name = req.name.strip()
        if not name:
            return fail("声音名称不能为空")
        item.name = name
    if req.sort_order is not None:
        item.sort_order = req.sort_order
    if req.enabled is not None:
        item.enabled = req.enabled
    item.updated_at = utc_now()
    db.add(
        audit_log(
            current_admin,
            "update_heygen_voice",
            "heygen_voice",
            item.id,
            {
                "voice_id": item.voice_id,
                "name": item.name,
                "enabled": item.enabled,
                "sort_order": item.sort_order,
            },
        )
    )
    await db.commit()
    await db.refresh(item)
    return success(heygen_voice_payload(item))


@router.post("/heygen-resources/sync", response_model=Response)
async def sync_system_heygen_resources(
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await sync_heygen_resources(db)
        db.add(
            audit_log(
                current_admin,
                "sync_heygen_resources",
                "heygen_resource",
                "system",
                result,
            )
        )
        await db.commit()
    except (HeygenConfigError, ValueError) as exc:
        await db.rollback()
        return fail(str(exc))
    except httpx.HTTPError:
        await db.rollback()
        return fail("HeyGen 资源同步失败，请稍后重试")
    except Exception:
        await db.rollback()
        return fail("HeyGen 资源同步失败，请稍后重试")

    return success(result)


async def _get_heygen_avatar(db: AsyncSession, avatar_row_id: str) -> HeygenAvatar | None:
    result = await db.execute(select(HeygenAvatar).where(HeygenAvatar.id == avatar_row_id))
    return result.scalar_one_or_none()


async def _get_heygen_voice(db: AsyncSession, voice_row_id: str) -> HeygenVoice | None:
    result = await db.execute(select(HeygenVoice).where(HeygenVoice.id == voice_row_id))
    return result.scalar_one_or_none()
