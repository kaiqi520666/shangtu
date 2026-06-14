from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_token, hash_password, verify_password
from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas.response import Response, fail, success

router = APIRouter(prefix="/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _user_payload(user: User) -> dict:
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "credits": user.credits,
    }


def _auth_payload(user: User) -> dict:
    return {
        "token": create_token(user.id),
        **_user_payload(user),
    }


@router.post("/register", response_model=Response)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        return fail("邮箱已注册")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
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
    return success(_auth_payload(user))


@router.get("/me", response_model=Response)
async def me(current_user: User = Depends(get_current_user)):
    return success(_user_payload(current_user))
