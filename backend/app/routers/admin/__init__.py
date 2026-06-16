from fastapi import APIRouter

from . import audit, billing, image_tasks, overview, settings, users

router = APIRouter(prefix="/admin", tags=["管理后台"])
router.include_router(overview.router)
router.include_router(users.router)
router.include_router(billing.router)
router.include_router(image_tasks.router)
router.include_router(settings.router)
router.include_router(audit.router)
