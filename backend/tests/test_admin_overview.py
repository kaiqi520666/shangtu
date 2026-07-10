from unittest.mock import AsyncMock

import pytest

from app.routers.admin.overview import overview


@pytest.mark.asyncio
async def test_overview_combines_failed_image_and_video_tasks():
    db = AsyncMock()
    db.scalar = AsyncMock(side_effect=[10, 8, 2, 1, 3, 120, 5000, 1200, 4, 5, 6, 7])

    response = await overview(current_admin=object(), db=db)

    assert response.data["failed_tasks"] == 13
    assert response.data["today_tasks"] == 9
    assert "failed_image_tasks" not in response.data
