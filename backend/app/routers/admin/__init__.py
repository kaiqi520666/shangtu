from fastapi import APIRouter

from . import audit, billing, commission_withdrawals, coupon_codes, heygen_resources, heygen_translation_languages, image_tasks, outfit_models, overview, product_catalog, prompt_templates, settings, users

router = APIRouter(prefix="/admin", tags=["管理后台"])
router.include_router(overview.router)
router.include_router(users.router)
router.include_router(billing.router)
router.include_router(commission_withdrawals.router)
router.include_router(coupon_codes.router)
router.include_router(image_tasks.router)
router.include_router(heygen_resources.router)
router.include_router(heygen_translation_languages.router)
router.include_router(settings.router)
router.include_router(prompt_templates.router)
router.include_router(outfit_models.router)
router.include_router(product_catalog.router)
router.include_router(audit.router)
