import pytest
from fastapi import HTTPException

from backend.app import main


@pytest.mark.asyncio
async def test_send_new_rewards_notification_rejects_missing_app_id():
    req = main.SendRewardsNotificationRequest(app_id="", title="t", body="b", data={})

    with pytest.raises(HTTPException) as exc:
        await main.send_new_rewards_notification(req)

    assert exc.value.status_code == 400
    assert "app_id is required" in exc.value.detail


@pytest.mark.asyncio
async def test_send_new_rewards_notification_scopes_by_app_id(monkeypatch):
    def fake_list_push_tokens():
        return {
            "a": {"token": "token_a", "app_id": "gossip_energy", "notifications_enabled": True},
            "b": {"token": "token_b", "app_id": "gossip_energy", "notifications_enabled": True},
            "c": {"token": "token_c", "app_id": "travel_town", "notifications_enabled": True},
        }

    captured = {}

    async def fake_notify_new_rewards(push_tokens_dict, count=None, title=None, body=None, app_id=None):
        captured["tokens"] = push_tokens_dict
        captured["title"] = title
        captured["body"] = body
        captured["app_id"] = app_id
        return {"success": ["a", "b"], "failed": []}

    monkeypatch.setattr(main.mongo_storage, "list_push_tokens", fake_list_push_tokens)
    monkeypatch.setattr(main, "notify_new_rewards", fake_notify_new_rewards)

    req = main.SendRewardsNotificationRequest(
        app_id="gossip_energy",
        title="New links",
        body="Open app",
        data={},
    )
    result = await main.send_new_rewards_notification(req)

    assert result["success"] is True
    assert result["app_id"] == "gossip_energy"
    assert set(captured["tokens"].keys()) == {"a", "b"}
    assert captured["app_id"] == "gossip_energy"


@pytest.mark.asyncio
async def test_list_tokens_for_app_filters_gossip_energy(monkeypatch):
    def fake_list_push_tokens():
        return {
            "a": {
                "token_id": "a",
                "token": "token_a",
                "app_id": "gossip_energy",
                "notifications_enabled": True,
                "device_type": "android",
            },
            "b": {
                "token_id": "b",
                "token": "token_b",
                "app_id": "travel_town",
                "notifications_enabled": True,
                "device_type": "ios",
            },
            "c": {
                "token_id": "c",
                "token": "token_c",
                "app_id": "gossip_energy",
                "notifications_enabled": False,
                "device_type": "android",
            },
        }

    monkeypatch.setattr(main.mongo_storage, "list_push_tokens", fake_list_push_tokens)

    result = await main.list_tokens_for_app("gossip_energy")

    assert result["app_id"] == "gossip_energy"
    assert result["count"] == 2
    assert result["enabled"] == 1
    assert set(result["tokens"]) == {"a", "c"}


@pytest.mark.asyncio
async def test_list_tokens_for_app_returns_empty_when_none(monkeypatch):
    monkeypatch.setattr(main.mongo_storage, "list_push_tokens", lambda: {})

    result = await main.list_tokens_for_app("gossip_energy")

    assert result["app_id"] == "gossip_energy"
    assert result["count"] == 0
    assert result["enabled"] == 0
    assert result["tokens"] == []
