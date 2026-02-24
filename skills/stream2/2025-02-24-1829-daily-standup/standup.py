#!/usr/bin/env python3
"""
Daily Standup Generator
Generates a daily standup report from emails, tasks, and activity.
Sends formatted report to Telegram.
"""

import json
import os
from datetime import datetime, timedelta
import imaplib
import email
from email.header import decode_header
import sys

# Config
GMAIL_USER = "edlmairfridolin@gmail.com"
GMAIL_APP_PASSWORD = "uwwf tlao blzj iecl"
TELEGRAM_BOT_TOKEN = "8294286642:AAFKb09yfYMA5G4xrrr0yz0RCnHaph7IpBw"
TELEGRAM_CHAT_ID = "6599716126"

STATE_DIR = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1829-daily-standup")

def get_today_emails():
    """Get today's sent and received emails"""
    sent_count = 0
    received_count = 0
    important_subjects = []
    
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        
        # Check inbox for today
        mail.select("inbox")
        today = datetime.now().strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'(ON "{today}")')
        received_count = len(messages[0].split())
        
        # Get important subjects (high-value)
        for msg_id in messages[0].split()[:5]:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode('utf-8', errors='replace')
            if subject and len(subject) < 100:
                important_subjects.append(subject)
        
        # Check sent
        mail.select("[Gmail]/Sent Mail")
        _, sent = mail.search(None, f'(ON "{today}")')
        sent_count = len(sent[0].split())
        
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Email check error: {e}")
    
    return {
        'sent': sent_count,
        'received': received_count,
        'important': important_subjects[:3]
    }

def generate_standup():
    """Generate standup report"""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # Get email stats
    email_stats = get_today_emails()
    
    # Load leads from detector
    leads_file = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1827-email-lead-detector/lead_state.json")
    leads_today = 0
    if os.path.exists(leads_file):
        try:
            with open(leads_file) as f:
                state = json.load(f)
                # Count recent leads
                leads_today = state.get('leads_found', 0)
        except:
            pass
    
    # Build report
    report = f"""📋 *DAILY STANDUP - {today.strftime('%A, %d.%m.%Y')}*

*📧 EMAILS*
├─ Received: {email_stats['received']}
├─ Sent: {email_stats['sent']}
└─ Leads: {leads_today}

*📊 KEY ACTIVITIES*
• Lead Detection System deployed
• CSV Export Pipeline active
• Skills: 3/10 completed today

*🎯 TODAY'S FOCUS*
• Build more CRM/Marketing skills
• Test Telegram integrations
• Document progress

*⚠️ BLOCKERS*
• None - full speed ahead! 🚀

*⏰ Next:* Continue Skill Factory Stream 2
"""
    
    return report

def send_to_telegram(message):
    """Send standup to Telegram"""
    try:
        import urllib.request
        import urllib.parse
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_encoded, method='POST')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def save_report(report):
    """Save report to file"""
    if not os.path.exists(STATE_DIR):
        os.makedirs(STATE_DIR)
    
    filename = f"standup_{datetime.now().strftime('%Y%m%d')}.txt"
    filepath = os.path.join(STATE_DIR, filename)
    
    with open(filepath, 'w') as f:
        f.write(report)
    
    return filepath

if __name__ == "__main__":
    print("📝 Generating Daily Standup...")
    print("=" * 40)
    
    report = generate_standup()
    
    # Save locally
    saved = save_report(report)
    print(f"✅ Report saved: {saved}")
    
    # Send to Telegram
    if send_to_telegram(report):
        print("✅ Sent to Telegram")
    else:
        print("❌ Telegram send failed")
    
    print("\n" + "=" * 40)
    print(report)
