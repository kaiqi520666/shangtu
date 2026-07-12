from datetime import timedelta
import os

from jose import jwt
from passlib.context import CryptContext

from app.core.time import utc_now

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password(password: str) -> None:
    if len(password) < 6:
        raise ValueError("密码至少需要 6 个字符")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("密码不能超过 72 个字节")


def set_user_password(user, password: str) -> None:
    validate_password(password)
    user.password_hash = hash_password(password)
    user.auth_version += 1


def create_token(user_id: int, auth_version: int) -> str:
    expire = utc_now() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "ver": auth_version, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> tuple[int, int]:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload["sub"]), int(payload["ver"])
