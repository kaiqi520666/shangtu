import pytest

from app.core.rate_limit import increment_fixed_window
from tests.fake_redis import FakeRedis


@pytest.mark.asyncio
async def test_increment_fixed_window_sets_expiration_once():
    redis = FakeRedis()

    assert await increment_fixed_window(redis, "limit:user-1", 60) == 1
    redis.expirations["limit:user-1"] = 30
    assert await increment_fixed_window(redis, "limit:user-1", 60) == 2

    assert redis.expirations["limit:user-1"] == 30


@pytest.mark.asyncio
async def test_increment_fixed_window_repairs_missing_expiration():
    redis = FakeRedis()
    redis.values["limit:user-1"] = 4

    assert await increment_fixed_window(redis, "limit:user-1", 60) == 5
    assert redis.expirations["limit:user-1"] == 60
