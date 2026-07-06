import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.providers.heygen_provider import HeygenConfigError
from app.core.time import utc_now
from app.models import HeygenTranslationLanguage, User
from app.schemas.response import Response, fail, success
from app.services.heygen_resources import sync_heygen_translation_languages

from .schemas import UpdateHeygenTranslationLanguageRequest
from .utils import audit_log, heygen_translation_language_payload, page_payload

router = APIRouter()


@router.get("/heygen-translation-languages", response_model=Response)
async def list_heygen_translation_languages(
    page: int = 1,
    page_size: int = 20,
    active: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    _ = current_admin
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    conditions = [HeygenTranslationLanguage.archived_at.is_(None)]
    if active in {"true", "false"}:
        conditions.append(HeygenTranslationLanguage.enabled == (active == "true"))
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                HeygenTranslationLanguage.name.ilike(like),
                HeygenTranslationLanguage.display_name_zh.ilike(like),
            )
        )

    total_stmt = select(func.count()).select_from(HeygenTranslationLanguage)
    data_stmt = select(HeygenTranslationLanguage).order_by(
        HeygenTranslationLanguage.sort_order.asc(),
        HeygenTranslationLanguage.updated_at.desc(),
        HeygenTranslationLanguage.id.desc(),
    )
    for condition in conditions:
        total_stmt = total_stmt.where(condition)
        data_stmt = data_stmt.where(condition)

    total = int((await db.execute(total_stmt)).scalar_one() or 0)
    result = await db.execute(data_stmt.offset((page - 1) * page_size).limit(page_size))
    items = [heygen_translation_language_payload(item) for item in result.scalars().all()]
    return success(page_payload(items, total, page, page_size))


@router.patch("/heygen-translation-languages/{language_id}", response_model=Response)
async def update_heygen_translation_language(
    language_id: str,
    req: UpdateHeygenTranslationLanguageRequest,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(HeygenTranslationLanguage, language_id)
    if not item or item.archived_at is not None:
        return fail("翻译语言不存在")

    if req.display_name_zh is not None:
        display_name_zh = req.display_name_zh.strip()
        if not display_name_zh:
            return fail("中文展示名不能为空")
        item.display_name_zh = display_name_zh
    if req.sort_order is not None:
        item.sort_order = req.sort_order
    if req.enabled is not None:
        item.enabled = req.enabled
    item.updated_at = utc_now()
    db.add(
        audit_log(
            current_admin,
            "update_heygen_translation_language",
            "heygen_translation_language",
            item.id,
            {
                "name": item.name,
                "display_name_zh": item.display_name_zh,
                "enabled": item.enabled,
                "sort_order": item.sort_order,
            },
        )
    )
    await db.commit()
    await db.refresh(item)
    return success(heygen_translation_language_payload(item))


@router.post("/heygen-translation-languages/sync", response_model=Response)
async def sync_system_heygen_translation_languages(
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await sync_heygen_translation_languages(db)
        db.add(
            audit_log(
                current_admin,
                "sync_heygen_translation_languages",
                "heygen_translation_language",
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
        return fail("HeyGen 翻译语言同步失败，请稍后重试")
    except Exception:
        await db.rollback()
        return fail("HeyGen 翻译语言同步失败，请稍后重试")

    return success(result)
