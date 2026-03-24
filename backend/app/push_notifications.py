"""
Push Notifications Module - Firebase Cloud Messaging
Handles sending push notifications to registered devices via Firebase FCM
"""

import firebase_admin
from firebase_admin import credentials, messaging, exceptions as fb_exceptions
from typing import List, Dict, Any
import logging
import hashlib
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported app IDs for scoped notification sends.
# Per user requirement, both currently use the same credentials file path.
APP_ID_TO_FIREBASE_APP_NAME: Dict[str, str] = {
    "travel_town": "travel_town",
    "gossip_energy": "gossip_energy",
}

# Default credential file candidates per app_id.
# Cloud Run paths are checked first, then local project-root fallbacks.
APP_ID_CREDENTIAL_CANDIDATES: Dict[str, List[Path]] = {
    "travel_town": [
        Path("/app/firebase-adminsdk.json"),
        Path(__file__).parent.parent.parent / "firebase-adminsdk.json",
    ],
    "gossip_energy": [
        Path("/app/firebase-adminsdk-gossip-energy.json"),
        Path(__file__).parent.parent.parent / "firebase-adminsdk-gossip-energy.json",
    ],
}


def _should_cleanup_token_for_error(error_text: str) -> bool:
    """Return True when an FCM error indicates token should be removed from DB."""
    text = (error_text or "").lower()
    cleanup_markers = [
        "senderid mismatch",
        "sender id mismatch",
        "registration token is not a valid fcm registration token",
        "not registered",
        "requested entity was not found",
    ]
    return any(marker in text for marker in cleanup_markers)

def _resolve_credential_path_for_app(app_id: str) -> Path | None:
    """Resolve service-account path for a specific app_id.

    Priority:
    1) Optional explicit env override per app_id
       - travel_town: FIREBASE_CREDENTIALS_TRAVEL_TOWN_PATH
       - gossip_energy: FIREBASE_CREDENTIALS_GOSSIP_ENERGY_PATH
    2) Default candidate paths from APP_ID_CREDENTIAL_CANDIDATES
    """
    env_key = f"FIREBASE_CREDENTIALS_{app_id.upper().replace('-', '_')}_PATH"
    env_path = os.getenv(env_key)
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate
        logger.error(
            f"Credential override path from {env_key} not found: {candidate}"
        )

    candidates = APP_ID_CREDENTIAL_CANDIDATES.get(app_id, [])
    for candidate in candidates:
        if candidate.exists():
            return candidate

    logger.error(
        f"No Firebase service account key found for app_id '{app_id}'. "
        f"Checked {len(candidates)} default paths and env {env_key}."
    )
    return None


# Initialize Firebase Admin SDK
def initialize_firebase(app_id: str):
    """Initialize and return Firebase Admin app for a specific app_id."""
    try:
        app_name = APP_ID_TO_FIREBASE_APP_NAME.get(app_id)
        if not app_name:
            logger.error(f"Unsupported app_id '{app_id}' for Firebase send")
            return None

        # Return existing named app if already initialized
        try:
            return firebase_admin.get_app(app_name)
        except ValueError:
            pass

        cred_path = _resolve_credential_path_for_app(app_id)
        if not cred_path:
            return None

        cred = credentials.Certificate(str(cred_path))
        app = firebase_admin.initialize_app(cred, name=app_name)
        logger.info(
            f"Firebase Admin SDK initialized successfully for app_id '{app_id}' from {cred_path}"
        )
        return app
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        return None


def _cleanup_stale_token(raw_token: str) -> None:
    """
    Delete a stale/unregistered FCM token from MongoDB.
    Called automatically when FCM reports a token as unregistered.
    """
    try:
        from . import mongo_storage  # lazy import to avoid circular dependency
        token_id = hashlib.sha256(raw_token.encode()).hexdigest()
        deleted = mongo_storage.delete_push_token(token_id)
        if deleted:
            logger.info(f"[CLEANUP] Removed stale token {token_id[:16]}... from DB")
        else:
            logger.warning(f"[CLEANUP] Stale token {token_id[:16]}... not found in DB")
    except Exception as e:
        logger.error(f"[CLEANUP] Failed to remove stale token: {e}")


async def send_push_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Dict[str, Any] = None,
    app_id: str = None,
) -> Dict[str, Any]:
    """
    Send push notification to multiple FCM tokens
    
    Args:
        tokens: List of FCM device tokens
        title: Notification title
        body: Notification body
        data: Optional data payload (for navigation, etc.)
    
    Returns:
        Dict with success/failed token lists
    """
    if not tokens:
        return {"success": [], "failed": [], "error": "No tokens provided"}
    
    if not app_id:
        return {"success": [], "failed": [], "error": "app_id is required"}

    # Initialize Firebase app for scoped app_id
    fb_app = initialize_firebase(app_id)
    if not fb_app:
        return {
            "success": [],
            "failed": [],
            "error": f"Firebase not initialized for app_id '{app_id}'",
        }
    
    results = {"success": [], "failed": []}
    
    # Create notification message
    notification = messaging.Notification(
        title=title,
        body=body
    )
    
    # Convert data values to strings (FCM requirement)
    fcm_data = {k: str(v) for k, v in (data or {}).items()}
    
    # Send to each token
    for token in tokens:
        try:
            message = messaging.Message(
                notification=notification,
                data=fcm_data,
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='default',
                        priority='high'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )
            
            # Send message
            response = messaging.send(message, app=fb_app)
            results["success"].append(token[:20] + "...")
            logger.info(f"FCM notification sent successfully: {response}")
            
        except messaging.UnregisteredError:
            error_msg = "Token unregistered"
            results["failed"].append({
                "token": token[:20] + "...",
                "error": error_msg
            })
            logger.warning(f"Token unregistered: {token[:20]}... — removing from DB")
            _cleanup_stale_token(token)
            
        except fb_exceptions.InvalidArgumentError as e:
            error_msg = f"Invalid argument: {str(e)}"
            results["failed"].append({
                "token": token[:20] + "...",
                "error": error_msg
            })
            logger.error(f"Invalid FCM argument: {error_msg}")
            if _should_cleanup_token_for_error(error_msg):
                logger.warning(f"Invalid/foreign token: {token[:20]}... — removing from DB")
                _cleanup_stale_token(token)
            
        except Exception as e:
            error_msg = str(e)
            results["failed"].append({
                "token": token[:20] + "...",
                "error": error_msg
            })
            logger.error(f"Failed to send FCM notification: {error_msg}")
            if _should_cleanup_token_for_error(error_msg):
                logger.warning(f"Sender/project mismatch token: {token[:20]}... — removing from DB")
                _cleanup_stale_token(token)
    
    return results


async def send_multicast_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Dict[str, Any] = None,
    app_id: str = None,
) -> Dict[str, Any]:
    """
    Send push notification to multiple tokens using multicast (more efficient)
    
    Args:
        tokens: List of FCM device tokens (max 500)
        title: Notification title
        body: Notification body
        data: Optional data payload
    
    Returns:
        Dict with success/failed counts and details
    """
    if not tokens:
        return {"success": [], "failed": [], "error": "No tokens provided"}
    
    if not app_id:
        return {"success": [], "failed": [], "error": "app_id is required"}

    # Initialize Firebase app for scoped app_id
    fb_app = initialize_firebase(app_id)
    if not fb_app:
        return {
            "success": [],
            "failed": [],
            "error": f"Firebase not initialized for app_id '{app_id}'",
        }
    
    # Convert data values to strings
    fcm_data = {k: str(v) for k, v in (data or {}).items()}
    
    # Create multicast message
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        data=fcm_data,
        tokens=tokens[:500],  # FCM limit is 500 tokens per request
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                channel_id='default',
                priority='high'
            )
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound='default',
                    badge=1
                )
            )
        )
    )
    
    try:
        # send_each_for_multicast uses the FCM v1 API (send_multicast is deprecated - old /batch endpoint returns 404)
        response = messaging.send_each_for_multicast(message, app=fb_app)
        
        results = {"success": [], "failed": []}
        
        # Process responses
        for idx, resp in enumerate(response.responses):
            token = tokens[idx]
            if resp.success:
                results["success"].append(token[:20] + "...")
            else:
                error_str = str(resp.exception) if resp.exception else "Unknown error"
                results["failed"].append({
                    "token": token[:20] + "...",
                    "error": error_str
                })
                # Auto-cleanup unregistered tokens
                if isinstance(resp.exception, messaging.UnregisteredError):
                    logger.warning(f"Token unregistered: {token[:20]}... — removing from DB")
                    _cleanup_stale_token(token)
                elif _should_cleanup_token_for_error(error_str):
                    logger.warning(f"Invalid/foreign token from multicast: {token[:20]}... — removing from DB")
                    _cleanup_stale_token(token)
        
        logger.info(f"FCM multicast sent: {response.success_count} success, {response.failure_count} failed")
        return results
        
    except Exception as e:
        logger.error(f"Failed to send FCM multicast: {str(e)}")
        return {"success": [], "failed": [], "error": str(e)}


async def notify_new_rewards(
    push_tokens_dict: dict,
    count: int = None,
    title: str = None,
    body: str = None,
    app_id: str = None,
) -> Dict[str, Any]:
    """
    Send notification about new rewards to all registered devices.

    Args:
        push_tokens_dict: Dictionary of registered push tokens (token_id -> data).
                          Tokens with notifications_enabled=False are filtered out automatically.
        count: Optional number of new rewards (used in default body text)
        title: Optional notification title override (falls back to default)
        body: Optional notification body override (falls back to default)

    Returns:
        Dict with notification send results
    """
    if not app_id:
        return {"success": [], "failed": [], "message": "app_id is required"}

    if app_id not in APP_ID_TO_FIREBASE_APP_NAME:
        return {
            "success": [],
            "failed": [],
            "message": f"Unsupported app_id '{app_id}'",
        }

    # Filter tokens by app_id and notifications_enabled=True
    tokens_list = [
        data["token"]
        for data in push_tokens_dict.values()
        if data.get("notifications_enabled", True) and data.get("app_id") == app_id
    ]

    if not tokens_list:
        logger.warning("No push tokens registered for notification or all tokens disabled")
        return {"success": [], "failed": [], "message": "No tokens registered or notifications disabled"}

    title = title or "New Rewards Available! 🎁"
    body = body or (f"{count} new rewards added!" if count else "Check out the latest rewards")
    
    logger.info(f"Sending FCM notification to {len(tokens_list)} devices")
    
    # Use multicast for better performance if many tokens
    if len(tokens_list) > 10:
        result = await send_multicast_notification(
            tokens=tokens_list,
            title=title,
            body=body,
            data={"screen": "Rewards"},
            app_id=app_id,
        )
    else:
        result = await send_push_notification(
            tokens=tokens_list,
            title=title,
            body=body,
            data={"screen": "Rewards"},
            app_id=app_id,
        )
    
    result["message"] = f"Sent to {len(result['success'])}/{len(tokens_list)} devices"
    return result
