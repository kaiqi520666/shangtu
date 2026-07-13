from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_token, hash_password, validate_password, verify_password
from app.core.config import require_env
from app.core.deps import get_current_user, get_db
from app.core.distribution import generate_invite_code
from app.core.providers.turnstile import TurnstileVerificationError, verify_turnstile
from app.core.time import to_utc_iso
from app.models import User
from app.schemas.response import Response, fail, success
from app.services.email_verification import (
    COOLDOWN_SECONDS,
    EmailVerificationError,
    consume_registration_code,
    issue_registration_code,
    normalize_email,
)
from app.services.login_security import (
    LoginSecurityState,
    clear_login_failures,
    get_login_security_state,
    record_login_failure,
)

router = APIRouter(prefix="/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    verification_code: str
    invite_code: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str
    captcha_token: str | None = None


class EmailCodeRequest(BaseModel):
    email: str
    captcha_token: str


def _client_ip(request: Request) -> str:
    return request.headers.get("x-real-ip") or (
        request.client.host if request.client else "unknown"
    )


def _login_security_payload(state: LoginSecurityState) -> dict:
    data = {"captcha_required": state.captcha_required}
    if state.retry_after_seconds is not None:
        data["retry_after_seconds"] = state.retry_after_seconds
    return data


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


@router.get("/captcha-config", response_model=Response)
async def captcha_config():
    return success({"site_key": require_env("TURNSTILE_SITE_KEY")})


@router.post("/email-code", response_model=Response)
async def send_email_code(
    req: EmailCodeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        await issue_registration_code(
            db,
            request.app.state.redis_pool,
            req.email,
            _client_ip(request),
            req.captcha_token,
        )
    except EmailVerificationError as exc:
        return fail(str(exc))
    return success({"cooldown_seconds": COOLDOWN_SECONDS}, "验证码已发送")


@router.post("/register", response_model=Response)
async def register(
    req: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        validate_password(req.password)
        email = normalize_email(req.email)
    except ValueError as exc:
        return fail(str(exc))
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        return fail("邮箱已注册")

    inviter = None
    if req.invite_code:
        inviter = (
            await db.execute(select(User).where(User.invite_code == req.invite_code.strip()))
        ).scalar_one_or_none()
        if not inviter or not inviter.distribution_enabled or inviter.distribution_level not in {1, 2}:
            return fail("邀请链接已失效")

    try:
        await consume_registration_code(
            request.app.state.redis_pool,
            email,
            req.verification_code,
        )
    except EmailVerificationError as exc:
        return fail(str(exc))

    user = User(
        username=req.username,
        email=email,
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
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        email = normalize_email(req.email)
    except EmailVerificationError as exc:
        return fail(str(exc))
    redis = request.app.state.redis_pool
    ip_address = _client_ip(request)
    security = await get_login_security_state(redis, email, ip_address)
    if security.rate_limited:
        return fail("登录尝试过于频繁，请稍后再试", data=_login_security_payload(security))
    if security.captcha_required:
        try:
            await verify_turnstile(req.captcha_token or "", ip_address, "login")
        except TurnstileVerificationError as exc:
            return fail(str(exc), data=_login_security_payload(security))

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        security = await record_login_failure(redis, email, ip_address)
        message = "登录尝试过于频繁，请稍后再试" if security.rate_limited else "邮箱或密码错误"
        return fail(message, data=_login_security_payload(security))
    await clear_login_failures(redis, email, ip_address)
    if user.status != "active":
        return fail("账号已被禁用，请联系管理员")
    return success(_auth_payload(user))


@router.get("/me", response_model=Response)
async def me(current_user: User = Depends(get_current_user)):
    return success(_user_payload(current_user))
