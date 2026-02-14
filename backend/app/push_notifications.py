"""
Push Notifications Module
Handles sending push notifications to registered devices via Expo Push API
"""

import httpx
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_push_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Send push notification to multiple Expo push tokens
    
    Args:
        tokens: List of Expo push tokens
        title: Notification title
        body: Notification body
        data: Optional data payload (for navigation, etc.)
    
    Returns:
        Dict with success/failed token lists
    """
    if not tokens:
        return {"success": [], "failed": [], "error": "No tokens provided"}
    
    messages = []
    for token in tokens:
        messages.append({
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
            "data": data or {},
            "priority": "high",
            "channelId": "default"
        })
    
    results = {"success": [], "failed": []}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                EXPO_PUSH_URL,
                json=messages,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                response_data = response.json()
                for i, result in enumerate(response_data.get("data", [])):
                    if result.get("status") == "ok":
                        results["success"].append(tokens[i])
                        logger.info(f"Notification sent successfully to {tokens[i][:20]}...")
                    else:
                        error_msg = result.get("message", "Unknown error")
                        results["failed"].append({
                            "token": tokens[i][:20] + "...",
                            "error": error_msg
                        })
                        logger.warning(f"Failed to send notification: {error_msg}")
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                results["failed"] = [{"error": error_msg}]
                logger.error(f"Expo Push API error: {error_msg}")
                
        except Exception as e:
            error_msg = str(e)
            results["failed"] = [{"error": error_msg}]
            logger.error(f"Exception sending notifications: {error_msg}")
    
    return results


async def notify_new_rewards(push_tokens_dict: dict, count: int = None) -> Dict[str, Any]:
    """
    Send notification about new rewards to all registered devices
    
    Args:
        push_tokens_dict: Dictionary of registered push tokens
        count: Optional number of new rewards
    
    Returns:
        Dict with notification send results
    """
    tokens_list = [data["token"] for data in push_tokens_dict.values()]
    
    if not tokens_list:
        logger.warning("No push tokens registered for notification")
        return {"success": False, "message": "No tokens registered"}
    
    title = "New Rewards Available! 🎁"
    body = f"{count} new rewards added!" if count else "Check out the latest rewards"
    
    logger.info(f"Sending notification to {len(tokens_list)} devices")
    
    result = await send_push_notification(
        tokens=tokens_list,
        title=title,
        body=body,
        data={"screen": "Rewards"}
    )
    
    result["message"] = f"Sent to {len(result['success'])}/{len(tokens_list)} devices"
    return result
