import pytest

from backend.app import main


@pytest.mark.asyncio
async def test_get_domino_rewards_uses_post_259_and_static_label(monkeypatch):
    captured = {}

    def fake_build_rewards_response(post_id: int, static_label=None):
        captured["post_id"] = post_id
        captured["static_label"] = static_label
        return {"success": True, "data": []}

    monkeypatch.setattr(main, "_build_rewards_response", fake_build_rewards_response)

    result = await main.get_domino_rewards()

    assert result["success"] is True
    assert captured["post_id"] == 259
    assert captured["static_label"] == "2X Free Coins"
