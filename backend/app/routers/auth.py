from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_token, hash_password, validate_password, verify_password
from app.core.deps import get_current_user, get_db
from app.core.distribution import generate_invite_code
from app.core.time import to_utc_iso
from app.models import User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    invite_code: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


def _user_payload(user: User) -> dict:
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "credits": user.credits,
        "role": user.role,
        "status": user.status,
        "consumption_multiplier": float(user.consumption_multiplier),
        "distribution_level": user.distribution_level,
        "distribution_enabled": user.distribution_enabled,
        "created_at": to_utc_iso(user.created_at),
    }


def _auth_payload(user: User) -> dict:
    return {
        "token": create_token(user.id, user.auth_version),
        **_user_payload(user),
    }


@router.post("/register", response_model=Response)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        validate_password(req.password)
    except ValueError as exc:
        return fail(str(exc))
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        return fail("邮箱已注册")

    inviter = None
    if req.invite_code:
        inviter = (
            await db.execute(select(User).where(User.invite_code == req.invite_code.strip()))
        ).scalar_one_or_none()
        if not inviter or not inviter.distribution_enabled or inviter.distribution_level not in {1, 2}:
            return fail("邀请链接已失效")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        distribution_level=inviter.distribution_level + 1 if inviter else None,
        distribution_parent_id=inviter.id if inviter else None,
        commission_rate=0 if inviter else None,
        invite_code=generate_invite_code() if inviter and inviter.distribution_level == 1 else None,
        distribution_enabled=bool(inviter),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return success(_auth_payload(user))


@router.post("/login", response_model=Response)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        return fail("邮箱或密码错误")
    if user.status != "active":
        return fail("账号已被禁用，请联系管理员")
    return success(_auth_payload(user))


@router.get("/me", response_model=Response)
async def me(current_user: User = Depends(get_current_user)):
    return success(_user_payload(current_user))
