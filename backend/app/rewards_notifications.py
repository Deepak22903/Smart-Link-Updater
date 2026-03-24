"""Utilities for post-specific rewards push notifications."""

from typing import Any, Dict
import logging

from . import mongo_storage
from .push_notifications import notify_new_rewards


# Mapping of post_id -> app_id for push notifications.
# When new links are added for a post, only devices registered with the matching
# app_id will receive a notification.
POST_NOTIFICATION_APP_MAP: Dict[int, str] = {
    206: "travel_town",  # Travel Town rewards app
    1149: "gossip_energy",  # Gossip Energy rewards app
}


def is_notifications_enabled(config: Dict[str, Any] | None) -> bool:
    """Robust check for notification toggle from post config."""
    if not config:
        return False

    value = config.get("send_notifications", False)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


async def notify_rewards_update_for_post(post_id: int, links_added: int) -> None:
    """Send a rewards notification to tokens belonging to the post's mapped app."""
    if links_added <= 0:
        return

    app_id = POST_NOTIFICATION_APP_MAP.get(post_id)
    if not app_id:
        logging.info(
            f"[NOTIFY] No app_id mapping for post {post_id} in POST_NOTIFICATION_APP_MAP, skipping notification"
        )
        return

    try:
        all_tokens = mongo_storage.list_push_tokens()  # Dict[token_id, data]
        app_tokens = {
            tid: data
            for tid, data in all_tokens.items()
            if data.get("app_id") == app_id
        }

        if not app_tokens:
            logging.info(
                f"[NOTIFY] No tokens registered for app_id='{app_id}' (post {post_id}), skipping"
            )
            return

        result = await notify_new_rewards(app_tokens, count=links_added, app_id=app_id)
        sent = len(result.get("success", []))
        failed = len(result.get("failed", []))
        logging.info(
            f"[NOTIFY] Post {post_id} (app='{app_id}'): Notified {sent}/{sent + failed} devices, {links_added} new links"
        )
    except Exception as e:
        logging.error(f"[NOTIFY] Failed to send notification for post {post_id}: {e}")
