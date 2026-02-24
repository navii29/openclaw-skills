#!/usr/bin/env python3
"""
Test email connection before going live
"""
import os
import sys
import imaplib
import smtplib
import ssl

CONFIG_FILE = os.path.expanduser("~/.openclaw/workspace/inbox-ai-config.env")

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    return config

def test_connection():
    config = load_config()
    
    print("🔍 Testing Inbox AI Configuration...")
    print(f"   Config file: {CONFIG_FILE}")
    
    # Check required fields
    required = ['IMAP_SERVER', 'SMTP_SERVER', 'EMAIL_USERNAME', 'EMAIL_PASSWORD']
    missing = [f for f in required if f not in config]
    if missing:
        print(f"\n❌ MISSING CONFIG: {', '.join(missing)}")
        return False
    
    print(f"\n   Email: {config['EMAIL_USERNAME']}")
    print(f"   IMAP: {config['IMAP_SERVER']}:{config.get('IMAP_PORT', 993)}")
    print(f"   SMTP: {config['SMTP_SERVER']}:{config.get('SMTP_PORT', 587)}")
    
    # Test IMAP
    print("\n📥 Testing IMAP connection...")
    try:
        imap = imaplib.IMAP4_SSL(config['IMAP_SERVER'], int(config.get('IMAP_PORT', 993)))
        imap.login(config['EMAIL_USERNAME'], config['EMAIL_PASSWORD'])
        imap.select('INBOX')
        status, count = imap.search(None, 'ALL')
        print(f"   ✅ IMAP connected! ({len(count[0].split())} total emails)")
        imap.logout()
    except Exception as e:
        print(f"   ❌ IMAP failed: {e}")
        return False
    
    # Test SMTP
    print("\n📤 Testing SMTP connection...")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(config['SMTP_SERVER'], int(config.get('SMTP_PORT', 587))) as server:
            server.starttls(context=context)
            server.login(config['EMAIL_USERNAME'], config['EMAIL_PASSWORD'])
            print(f"   ✅ SMTP connected!")
    except Exception as e:
        print(f"   ❌ SMTP failed: {e}")
        return False
    
    print("\n✅ All tests passed! Ready for deployment.")
    return True

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
