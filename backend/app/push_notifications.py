"""
Push Notifications Module - Firebase Cloud Messaging
Handles sending push notifications to registered devices via Firebase FCM
"""

import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Dict, Any
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account"""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Try Cloud Run secret mount path first
            cred_path = Path("/app/firebase-adminsdk.json")
            
            # Fallback to local development path
            if not cred_path.exists():
                cred_path = Path(__file__).parent.parent.parent / "firebase-adminsdk.json"
            
            if not cred_path.exists():
                logger.error(f"Firebase service account key not found at {cred_path}")
                logger.error("Checked paths: /app/firebase-adminsdk.json and project root")
                return False
            
            cred = credentials.Certificate(str(cred_path))
            firebase_admin.initialize_app(cred)
            logger.info(f"Firebase Admin SDK initialized successfully from {cred_path}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        return False


async def send_push_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Dict[str, Any] = None
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
    
    # Initialize Firebase if needed
    if not initialize_firebase():
        return {"success": [], "failed": [], "error": "Firebase not initialized"}
    
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
            response = messaging.send(message)
            results["success"].append(token[:20] + "...")
            logger.info(f"FCM notification sent successfully: {response}")
            
        except messaging.UnregisteredError:
            error_msg = "Token unregistered"
            results["failed"].append({
                "token": token[:20] + "...",
                "error": error_msg
            })
            logger.warning(f"Token unregistered: {token[:20]}...")
            
        except messaging.InvalidArgumentError as e:
            error_msg = f"Invalid argument: {str(e)}"
            results["failed"].append({
                "token": token[:20] + "...",
                "error": error_msg
            })
            logger.error(f"Invalid FCM argument: {error_msg}")
            
        except Exception as e:
            error_msg = str(e)
            results["failed"].append({
                "token": token[:20] + "...",
                "error": error_msg
            })
            logger.error(f"Failed to send FCM notification: {error_msg}")
    
    return results


async def send_multicast_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Dict[str, Any] = None
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
    
    # Initialize Firebase if needed
    if not initialize_firebase():
        return {"success": [], "failed": [], "error": "Firebase not initialized"}
    
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
        # Send to all tokens at once
        response = messaging.send_multicast(message)
        
        results = {"success": [], "failed": []}
        
        # Process responses
        for idx, resp in enumerate(response.responses):
            token = tokens[idx]
            if resp.success:
                results["success"].append(token[:20] + "...")
            else:
                results["failed"].append({
                    "token": token[:20] + "...",
                    "error": str(resp.exception) if resp.exception else "Unknown error"
                })
        
        logger.info(f"FCM multicast sent: {response.success_count} success, {response.failure_count} failed")
        return results
        
    except Exception as e:
        logger.error(f"Failed to send FCM multicast: {str(e)}")
        return {"success": [], "failed": [], "error": str(e)}


async def notify_new_rewards(push_tokens_dict: dict, count: int = None) -> Dict[str, Any]:
    """
    Send notification about new rewards to all registered devices
    
    Args:
        push_tokens_dict: Dictionary of registered push tokens
        count: Optional number of new rewards
    
    Returns:
        Dict with notification send results
    """
    # Filter tokens to only those with notifications_enabled set to True (default True)
    tokens_list = [data["token"] for data in push_tokens_dict.values() if data.get("notifications_enabled", True)]
    
    if not tokens_list:
        logger.warning("No push tokens registered for notification or all tokens disabled")
        return {"success": False, "message": "No tokens registered or notifications disabled"}
    
    title = "New Rewards Available! 🎁"
    body = f"{count} new rewards added!" if count else "Check out the latest rewards"
    
    logger.info(f"Sending FCM notification to {len(tokens_list)} devices")
    
    # Use multicast for better performance if many tokens
    if len(tokens_list) > 10:
        result = await send_multicast_notification(
            tokens=tokens_list,
            title=title,
            body=body,
            data={"screen": "Rewards"}
        )
    else:
        result = await send_push_notification(
            tokens=tokens_list,
            title=title,
            body=body,
            data={"screen": "Rewards"}
        )
    
    result["message"] = f"Sent to {len(result['success'])}/{len(tokens_list)} devices"
    return result
