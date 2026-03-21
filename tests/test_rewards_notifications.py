import pytest

from backend.app import rewards_notifications


def test_is_notifications_enabled_truthy_values():
    assert rewards_notifications.is_notifications_enabled({"send_notifications": True}) is True
    assert rewards_notifications.is_notifications_enabled({"send_notifications": "true"}) is True
    assert rewards_notifications.is_notifications_enabled({"send_notifications": "1"}) is True
    assert rewards_notifications.is_notifications_enabled({"send_notifications": "yes"}) is True


def test_is_notifications_enabled_falsy_values():
    assert rewards_notifications.is_notifications_enabled({"send_notifications": False}) is False
    assert rewards_notifications.is_notifications_enabled({"send_notifications": "false"}) is False
    assert rewards_notifications.is_notifications_enabled({"send_notifications": 0}) is False
    assert rewards_notifications.is_notifications_enabled({}) is False
    assert rewards_notifications.is_notifications_enabled(None) is False


@pytest.mark.asyncio
async def test_notify_rewards_update_filters_by_app_id(monkeypatch):
    sent = {}

    def fake_list_push_tokens():
        return {
            "a": {"token": "token_a", "app_id": "travel_town", "notifications_enabled": True},
            "b": {"token": "token_b", "app_id": "travel_town", "notifications_enabled": True},
            "c": {"token": "token_c", "app_id": "other_app", "notifications_enabled": True},
        }

    async def fake_notify_new_rewards(push_tokens_dict, count=None, title=None, body=None):
        sent["tokens"] = push_tokens_dict
        sent["count"] = count
        return {"success": ["ok"], "failed": []}

    monkeypatch.setattr(rewards_notifications.mongo_storage, "list_push_tokens", fake_list_push_tokens)
    monkeypatch.setattr(rewards_notifications, "notify_new_rewards", fake_notify_new_rewards)

    await rewards_notifications.notify_rewards_update_for_post(206, 3)

    assert set(sent["tokens"].keys()) == {"a", "b"}
    assert sent["count"] == 3


@pytest.mark.asyncio
async def test_notify_rewards_update_skips_unmapped_post(monkeypatch):
    called = {"list": 0}

    def fake_list_push_tokens():
        called["list"] += 1
        return {}

    monkeypatch.setattr(rewards_notifications.mongo_storage, "list_push_tokens", fake_list_push_tokens)

    await rewards_notifications.notify_rewards_update_for_post(999999, 2)

    assert called["list"] == 0
