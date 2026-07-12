from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import (
    create_token,
    decode_token,
    hash_password,
    set_user_password,
    validate_password,
    verify_password,
)
from app.core.deps import get_current_super_admin, get_current_user
from app.routers.account import ChangePasswordRequest, change_password
from app.routers.admin.schemas import ResetUserPasswordRequest
from app.routers.admin.users import reset_user_password


def user(**overrides):
    values = {
        "id": 1,
        "email": "user@example.com",
        "password_hash": hash_password("old-password"),
        "auth_version": 0,
        "status": "active",
        "role": "user",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def db_for(target):
    result = Mock()
    result.scalar_one.return_value = target
    result.scalar_one_or_none.return_value = target
    return SimpleNamespace(execute=AsyncMock(return_value=result), add=Mock(), commit=AsyncMock())


def test_password_rules_cover_characters_and_bcrypt_bytes():
    with pytest.raises(ValueError, match="6 个字符"):
        validate_password("12345")
    validate_password("密码1234")
    with pytest.raises(ValueError, match="72 个字节"):
        validate_password("密" * 25)


def test_password_update_increments_version_and_invalidates_old_token():
    target = user()
    old_token = create_token(target.id, target.auth_version)
    set_user_password(target, "new-password")

    assert target.auth_version == 1
    assert verify_password("new-password", target.password_hash)
    assert decode_token(old_token) == (target.id, 0)
    assert decode_token(create_token(target.id, target.auth_version)) == (target.id, 1)


@pytest.mark.asyncio
async def test_get_current_user_rejects_stale_token():
    target = user(auth_version=2)
    db = db_for(target)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=create_token(target.id, 1)
    )

    with pytest.raises(HTTPException, match="登录状态已失效") as exc:
        await get_current_user(credentials, db)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_user_change_password_rejects_wrong_and_same_password():
    target = user()
    db = db_for(target)
    wrong = await change_password(
        ChangePasswordRequest(current_password="wrong", new_password="new-password"),
        target,
        db,
    )
    same = await change_password(
        ChangePasswordRequest(current_password="old-password", new_password="old-password"),
        target,
        db,
    )

    assert wrong.code != 0
    assert same.code != 0
    assert target.auth_version == 0
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_user_change_password_commits_hash_and_version():
    target = user()
    db = db_for(target)
    response = await change_password(
        ChangePasswordRequest(current_password="old-password", new_password="new-password"),
        target,
        db,
    )

    assert response.code == 0
    assert target.auth_version == 1
    assert verify_password("new-password", target.password_hash)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_reset_password_writes_password_free_audit():
    target = user()
    admin = user(id=99, email="admin@example.com", role="super_admin")
    db = db_for(target)
    response = await reset_user_password(
        target.id,
        ResetUserPasswordRequest(new_password="admin-reset"),
        admin,
        db,
    )

    audit = db.add.call_args.args[0]
    assert response.code == 0
    assert target.auth_version == 1
    assert audit.action == "reset_user_password"
    assert audit.target_id == str(target.id)
    assert audit.detail_json == "{}"


@pytest.mark.asyncio
async def test_admin_reset_missing_user_and_non_admin_access():
    missing_db = db_for(None)
    response = await reset_user_password(
        404,
        ResetUserPasswordRequest(new_password="admin-reset"),
        user(role="super_admin"),
        missing_db,
    )
    assert response.code != 0
    missing_db.commit.assert_not_awaited()

    with pytest.raises(HTTPException) as exc:
        await get_current_super_admin(user(role="user"))
    assert exc.value.status_code == 403
