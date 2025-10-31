"""
Notification System for HTML Monitoring Alerts

Supports:
- Email notifications (via SMTP)
- Webhook notifications (e.g., Slack, Discord, custom endpoints)
- Console logging for development
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import httpx
from datetime import datetime

from .models import Alert
from .html_monitor import get_monitor


class NotificationService:
    """Send notifications for monitoring alerts"""
    
    def __init__(self):
        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.alert_email_to = os.getenv("ALERT_EMAIL_TO", "")
        self.alert_email_from = os.getenv("ALERT_EMAIL_FROM", self.smtp_user)
        
        # Webhook configuration
        self.webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
        
        # Notification preferences
        self.enable_email = os.getenv("ENABLE_EMAIL_ALERTS", "false").lower() == "true"
        self.enable_webhook = os.getenv("ENABLE_WEBHOOK_ALERTS", "false").lower() == "true"
        self.enable_console = os.getenv("ENABLE_CONSOLE_ALERTS", "true").lower() == "true"
    
    async def send_alert(self, alert: Alert):
        """Send an alert via configured channels"""
        sent_channels = []
        
        # Console logging (always useful for development)
        if self.enable_console:
            self._log_to_console(alert)
            sent_channels.append("console")
        
        # Email
        if self.enable_email and self.smtp_user and self.alert_email_to:
            try:
                self._send_email(alert)
                sent_channels.append("email")
            except Exception as e:
                print(f"Failed to send email alert: {e}")
        
        # Webhook
        if self.enable_webhook and self.webhook_url:
            try:
                await self._send_webhook(alert)
                sent_channels.append("webhook")
            except Exception as e:
                print(f"Failed to send webhook alert: {e}")
        
        return sent_channels
    
    def _log_to_console(self, alert: Alert):
        """Log alert to console"""
        severity_icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨"
        }
        
        icon = severity_icons.get(alert.severity, "📢")
        
        print("\n" + "=" * 80)
        print(f"{icon} ALERT [{alert.severity.upper()}] - {alert.alert_type}")
        print("=" * 80)
        print(f"Source: {alert.source_url}")
        print(f"Message: {alert.message}")
        print(f"Time: {alert.timestamp}")
        
        if alert.details:
            print("\nDetails:")
            for key, value in alert.details.items():
                print(f"  {key}: {value}")
        
        print("=" * 80 + "\n")
    
    def _send_email(self, alert: Alert):
        """Send email alert"""
        subject = f"[{alert.severity.upper()}] SmartLink Alert: {alert.alert_type}"
        
        # Create HTML email body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: {'#ff4444' if alert.severity == 'critical' else '#ff9800' if alert.severity == 'warning' else '#2196F3'}; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                <h2 style="margin: 0;">⚠️ SmartLink Updater Alert</h2>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Severity: {alert.severity.upper()}</p>
            </div>
            
            <div style="border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 5px 5px;">
                <h3 style="color: #333; margin-top: 0;">Alert Type: {alert.alert_type}</h3>
                
                <p><strong>Source URL:</strong><br/>
                <a href="{alert.source_url}">{alert.source_url}</a></p>
                
                <p><strong>Message:</strong><br/>
                {alert.message}</p>
                
                <p><strong>Time:</strong><br/>
                {alert.timestamp}</p>
                
                {"<h4>Details:</h4><ul>" + "".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in alert.details.items()]) + "</ul>" if alert.details else ""}
                
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                
                <p style="font-size: 12px; color: #666;">
                    This is an automated alert from SmartLink Updater.<br/>
                    Check the <a href="{os.getenv('API_URL', 'http://localhost:8000')}/health/extractors">health dashboard</a> for more details.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.alert_email_from
        msg['To'] = self.alert_email_to
        
        # Add HTML part
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email
        # Use SMTP_SSL for port 465, or SMTP with STARTTLS for port 587
        if self.smtp_port == 465:
            # SSL connection (Hostinger, some providers)
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
        else:
            # STARTTLS connection (Gmail, most providers)
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
    
    async def _send_webhook(self, alert: Alert):
        """Send webhook notification (e.g., Slack, Discord)"""
        
        # Detect webhook type from URL
        if "slack.com" in self.webhook_url:
            payload = self._format_slack_message(alert)
        elif "discord.com" in self.webhook_url:
            payload = self._format_discord_message(alert)
        else:
            # Generic webhook format
            payload = alert.model_dump()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.webhook_url,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
    
    def _format_slack_message(self, alert: Alert) -> dict:
        """Format alert for Slack webhook"""
        color_map = {
            "info": "#2196F3",
            "warning": "#ff9800",
            "critical": "#ff4444"
        }
        
        fields = [
            {
                "title": "Alert Type",
                "value": alert.alert_type,
                "short": True
            },
            {
                "title": "Severity",
                "value": alert.severity.upper(),
                "short": True
            },
            {
                "title": "Source URL",
                "value": f"<{alert.source_url}|{alert.source_url[:50]}...>",
                "short": False
            }
        ]
        
        if alert.details:
            for key, value in alert.details.items():
                fields.append({
                    "title": key.replace("_", " ").title(),
                    "value": str(value),
                    "short": True
                })
        
        return {
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#666666"),
                    "title": "🔔 SmartLink Updater Alert",
                    "text": alert.message,
                    "fields": fields,
                    "footer": "SmartLink Updater",
                    "ts": int(datetime.fromisoformat(alert.timestamp).timestamp())
                }
            ]
        }
    
    def _format_discord_message(self, alert: Alert) -> dict:
        """Format alert for Discord webhook"""
        color_map = {
            "info": 2196211,  # Blue
            "warning": 16737280,  # Orange
            "critical": 16724736  # Red
        }
        
        fields = [
            {"name": "Alert Type", "value": alert.alert_type, "inline": True},
            {"name": "Severity", "value": alert.severity.upper(), "inline": True},
            {"name": "Source URL", "value": alert.source_url[:100], "inline": False}
        ]
        
        if alert.details:
            for key, value in list(alert.details.items())[:5]:  # Max 5 detail fields
                fields.append({
                    "name": key.replace("_", " ").title(),
                    "value": str(value)[:100],
                    "inline": True
                })
        
        return {
            "embeds": [
                {
                    "title": "🔔 SmartLink Updater Alert",
                    "description": alert.message,
                    "color": color_map.get(alert.severity, 7506394),
                    "fields": fields,
                    "timestamp": alert.timestamp,
                    "footer": {"text": "SmartLink Updater"}
                }
            ]
        }


# Global instance
_notification_service = None

def get_notification_service() -> NotificationService:
    """Get global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


async def process_unnotified_alerts():
    """
    Process all unnotified alerts and send notifications.
    
    This should be called periodically (e.g., via cron job or background task).
    """
    monitor = get_monitor()
    notifier = get_notification_service()
    
    alerts = monitor.get_unnotified_alerts()
    
    if not alerts:
        return {"processed": 0, "message": "No unnotified alerts"}
    
    sent_count = 0
    for alert in alerts:
        try:
            channels = await notifier.send_alert(alert)
            if channels:
                sent_count += 1
        except Exception as e:
            print(f"Failed to send alert: {e}")
    
    # Mark alerts as notified
    alert_ids = list(range(len(alerts)))
    monitor.mark_alerts_notified(alert_ids)
    
    return {
        "processed": sent_count,
        "total_alerts": len(alerts),
        "message": f"Sent {sent_count} notifications"
    }
