from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.core.media_projection import voiceover_task_payload
from app.core.system_settings import normalize_voiceover_credit_cost
from app.core.voiceover import calculate_voiceover_credit_cost, count_voiceover_characters
from app.worker.voiceover_tasks import refund_task_if_needed


@pytest.mark.parametrize(
    ("text", "expected"),
    [("你好，世界", 5), ("你 好\n世界\t", 4), ("   ", 0), ("hello world", 10)],
)
def test_count_voiceover_characters_ignores_whitespace(text, expected):
    assert count_voiceover_characters(text) == expected


@pytest.mark.parametrize(("characters", "unit_cost", "expected"), [(1, 1, 1), (100, 2, 2), (101, 2, 4), (5000, 1, 50)])
def test_calculate_voiceover_credit_cost_rounds_up(characters, unit_cost, expected):
    assert calculate_voiceover_credit_cost(characters, unit_cost) == expected


def test_normalize_voiceover_credit_cost():
    assert normalize_voiceover_credit_cost("3") == 3
    with pytest.raises(ValueError, match="大于等于1"):
        normalize_voiceover_credit_cost(0)


def test_voiceover_task_payload_uses_canonical_asset_url():
    task = SimpleNamespace(
        id="task-1",
        sort_order=2,
        status="done",
        progress=100,
        error_message=None,
        credit_cost=2,
        credit_refunded=False,
        settings_snapshot_json='{"voice_name":"龙安洋"}',
        created_at=None,
    )
    asset = SimpleNamespace(id="asset-1", audio_url="https://oss.example.com/audio.mp3")
    payload = voiceover_task_payload(task, asset)
    assert payload["result_url"] == asset.audio_url
    assert payload["asset_id"] == asset.id
    assert payload["media_type"] == "audio"


@pytest.mark.asyncio
async def test_voiceover_refund_is_idempotent():
    db = AsyncMock()
    task = SimpleNamespace(id="task-1", user_id=7, credit_cost=3, credit_refunded=False)
    with patch("app.worker.voiceover_tasks.refund_user_credits", AsyncMock(return_value=97)) as refund:
        assert await refund_task_if_needed(db, task) == 97
        assert await refund_task_if_needed(db, task) is None
    refund.assert_awaited_once_with(db, 7, 3, note="AI配音任务失败退回 · task-1")
