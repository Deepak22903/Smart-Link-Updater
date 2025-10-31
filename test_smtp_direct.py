#!/usr/bin/env python3
"""Quick SMTP test for Hostinger"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Hostinger SMTP settings
SMTP_HOST = "smtp.hostinger.com"
SMTP_PORT = 465
SMTP_USER = "support@peekdeep.com"
SMTP_PASSWORD = "Deepak@9175"
EMAIL_TO = "deepakshitole4@gmail.com"

print("Testing Hostinger SMTP connection...")
print(f"Host: {SMTP_HOST}")
print(f"Port: {SMTP_PORT}")
print(f"User: {SMTP_USER}")
print(f"Password: {'*' * len(SMTP_PASSWORD)}")

try:
    print("\nConnecting with SSL...")
    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
    print("✓ Connected")
    
    print("Logging in...")
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("✓ Login successful!")
    
    print("\nSending test email...")
    msg = MIMEMultipart()
    msg['Subject'] = 'SmartLink Test Email'
    msg['From'] = SMTP_USER
    msg['To'] = EMAIL_TO
    
    body = "This is a test email from SmartLink Updater monitoring system."
    msg.attach(MIMEText(body, 'plain'))
    
    server.send_message(msg)
    print(f"✓ Email sent to {EMAIL_TO}")
    
    server.quit()
    print("\n✅ All tests passed! Email configuration working.")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication failed: {e}")
    print("\nPossible issues:")
    print("1. Incorrect password")
    print("2. Email account security settings blocking access")
    print("3. Two-factor authentication enabled (need app-specific password)")
    print("\nTry:")
    print("1. Log into webmail.hostinger.com with these credentials")
    print("2. Check if 2FA is enabled")
    print("3. Check spam/security settings in Hostinger panel")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
