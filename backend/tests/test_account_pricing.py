from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.routers.account import account_pricing
from app.routers.billing import list_packages


@pytest.mark.asyncio
async def test_account_pricing_returns_all_base_costs_and_multiplier():
    user = SimpleNamespace(consumption_multiplier=Decimal("1.20"))
    with (
        patch("app.routers.account.get_effective_image_credit_costs", AsyncMock(return_value={"1K": 9})),
        patch("app.routers.account.get_effective_video_credit_costs", AsyncMock(return_value={"720p": 36})),
        patch("app.routers.account.get_effective_digital_human_credit_costs", AsyncMock(return_value={"standard": 7})),
        patch("app.routers.account.get_effective_digital_human_precharge_costs", AsyncMock(return_value={"standard": 2000})),
        patch("app.routers.account.get_effective_video_translation_credit_costs", AsyncMock(return_value={"standard": 7})),
        patch("app.routers.account.get_effective_voiceover_credit_cost", AsyncMock(return_value=1)),
    ):
        response = await account_pricing(user, AsyncMock())

    assert response.code == 0
    assert response.data["image_credit_costs"] == {"1K": 9}
    assert response.data["video_translation_credit_costs"] == {"standard": 7}
    assert response.data["voiceover_credit_cost_per_100_chars"] == 1
    assert response.data["consumption_multiplier"] == 1.2


@pytest.mark.asyncio
async def test_billing_packages_no_longer_mix_in_pricing_data():
    user = SimpleNamespace(credits=100)
    with patch(
        "app.routers.billing.get_effective_recharge_packages",
        AsyncMock(return_value=[{"id": "p1", "credits": 100}]),
    ):
        response = await list_packages(user, AsyncMock())

    assert response.code == 0
    assert response.data == {
        "packages": [{"id": "p1", "credits": 100}],
        "credits": 100,
    }
