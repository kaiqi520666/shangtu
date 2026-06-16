from fastapi import APIRouter

from . import billing, overview, users

router = APIRouter(prefix="/admin", tags=["管理后台"])
router.include_router(overview.router)
router.include_router(users.router)
router.include_router(billing.router)
