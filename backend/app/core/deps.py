from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_token
from app.core.database import SessionLocal
from app.models import User

security = HTTPBearer()


async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_id = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="token无效")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user


async def get_current_super_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="无权访问管理后台")
    return current_user
