#!/usr/bin/env python3
"""
Test Email Alerts Configuration

This script tests your SMTP email configuration without needing actual alerts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.models import Alert
from backend.app.notifications import get_notification_service


def test_email_config():
    """Test email configuration"""
    
    print("\n" + "=" * 80)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 80)
    
    # Check environment variables
    print("\n1. Checking environment variables...")
    
    required_vars = {
        'ENABLE_EMAIL_ALERTS': os.getenv('ENABLE_EMAIL_ALERTS'),
        'SMTP_HOST': os.getenv('SMTP_HOST'),
        'SMTP_PORT': os.getenv('SMTP_PORT'),
        'SMTP_USER': os.getenv('SMTP_USER'),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
        'ALERT_EMAIL_TO': os.getenv('ALERT_EMAIL_TO'),
    }
    
    missing = []
    for var, value in required_vars.items():
        if value and 'YOUR_' not in value.upper():
            print(f"   ✓ {var}: {value if var != 'SMTP_PASSWORD' else '***hidden***'}")
        else:
            print(f"   ✗ {var}: Not set or placeholder")
            missing.append(var)
    
    if missing:
        print(f"\n❌ Missing configuration: {', '.join(missing)}")
        print("\nPlease update .env with your Hostinger credentials:")
        print("   SMTP_PASSWORD=your_actual_email_password")
        return False
    
    # Check if email alerts are enabled
    if os.getenv('ENABLE_EMAIL_ALERTS', 'false').lower() != 'true':
        print("\n❌ Email alerts are disabled!")
        print("   Set ENABLE_EMAIL_ALERTS=true in .env")
        return False
    
    print("\n✓ All environment variables configured")
    
    # Test SMTP connection
    print("\n2. Testing SMTP connection...")
    
    import smtplib
    
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    try:
        if smtp_port == 465:
            print(f"   Connecting to {smtp_host}:{smtp_port} (SSL)...")
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                print("   ✓ Connected")
                print("   Logging in...")
                server.login(smtp_user, smtp_password)
                print("   ✓ Login successful")
        else:
            print(f"   Connecting to {smtp_host}:{smtp_port} (STARTTLS)...")
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                print("   ✓ Connected")
                print("   Starting TLS...")
                server.starttls()
                print("   ✓ TLS started")
                print("   Logging in...")
                server.login(smtp_user, smtp_password)
                print("   ✓ Login successful")
        
        print("\n✓ SMTP connection successful!")
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ SMTP Authentication Failed!")
        print("   Check your email and password in .env")
        print("   For Hostinger: Use your email password (not an app password)")
        return False
    except Exception as e:
        print(f"\n❌ SMTP Connection Failed: {e}")
        return False
    
    # Test sending actual alert
    print("\n3. Sending test alert email...")
    
    try:
        # Create a test alert
        test_alert = Alert(
            alert_type="test_alert",
            source_url="https://test.example.com",
            severity="info",
            message="This is a test alert from SmartLink Updater monitoring system",
            timestamp="2025-10-27T10:00:00.000000",
            notified=False,
            details={
                "test": "This is a test email",
                "smtp_host": smtp_host,
                "smtp_port": smtp_port,
                "from": smtp_user,
                "to": os.getenv('ALERT_EMAIL_TO')
            }
        )
        
        # Get notification service and send
        notifier = get_notification_service()
        
        # Temporarily enable email for this test
        original_enable = notifier.enable_email
        notifier.enable_email = True
        
        import asyncio
        channels = asyncio.run(notifier.send_alert(test_alert))
        
        notifier.enable_email = original_enable
        
        if 'email' in channels:
            print(f"\n✅ Test email sent successfully!")
            print(f"   From: {smtp_user}")
            print(f"   To: {os.getenv('ALERT_EMAIL_TO')}")
            print(f"   Subject: [INFO] SmartLink Alert: test_alert")
            print(f"\n   Check your inbox at {os.getenv('ALERT_EMAIL_TO')}")
            print("   (It might take a minute to arrive)")
            return True
        else:
            print("\n⚠️  Email not sent (check console output above)")
            return False
            
    except Exception as e:
        print(f"\n❌ Failed to send test email: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 80)
    print("🔔 SmartLink Updater - Email Alert Test")
    print("=" * 80)
    
    success = test_email_config()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ EMAIL ALERTS CONFIGURED SUCCESSFULLY!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Check your inbox at", os.getenv('ALERT_EMAIL_TO'))
        print("2. Add to spam whitelist if needed")
        print("3. Email alerts will now be sent automatically when:")
        print("   - Structure changes detected")
        print("   - Zero links extracted")
        print("   - Confidence drops significantly")
        print("   - Consecutive failures occur")
        print("\nManual trigger:")
        print("   curl -X POST http://localhost:8000/alerts/send")
        
    else:
        print("\n" + "=" * 80)
        print("❌ EMAIL CONFIGURATION NEEDS ATTENTION")
        print("=" * 80)
        print("\nPlease fix the issues above and run again:")
        print("   python3 test_email_alerts.py")


if __name__ == "__main__":
    main()
