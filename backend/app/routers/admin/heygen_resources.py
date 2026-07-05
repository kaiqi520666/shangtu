import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.models import User
from app.schemas.response import Response, fail, success
from app.services.heygen_resources import sync_heygen_resources
from app.core.providers.heygen_provider import HeygenConfigError

from .utils import audit_log

router = APIRouter()


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
