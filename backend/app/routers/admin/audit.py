from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin, get_db
from app.core.pagination import PaginationParams, execute_pagination, pagination_params
from app.models import AdminAuditLog, User
from app.schemas.response import Response, success

from .utils import audit_log_payload, page_payload

router = APIRouter()


@router.get("/audit-logs", response_model=Response)
async def list_audit_logs(
    pagination: PaginationParams = Depends(pagination_params),
    action: str | None = None,
    keyword: str | None = None,
    current_admin: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if action:
        conditions.append(AdminAuditLog.action == action.strip())
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                AdminAuditLog.action.ilike(like),
                AdminAuditLog.target_type.ilike(like),
                AdminAuditLog.target_id.ilike(like),
                AdminAuditLog.detail_json.ilike(like),
                User.email.ilike(like),
            )
        )

    total_stmt = (
        select(func.count())
        .select_from(AdminAuditLog)
        .outerjoin(User, User.id == AdminAuditLog.actor_user_id)
    )
    data_stmt = (
        select(AdminAuditLog, User)
        .outerjoin(User, User.id == AdminAuditLog.actor_user_id)
        .order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc())
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
    items = [audit_log_payload(log, actor) for log, actor in result.all()]
    return success(page_payload(items, total, pagination.page, pagination.page_size))
