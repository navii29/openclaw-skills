#!/usr/bin/env python3
"""
Smart Gmail Automation v3 - Silent Mode
Checks Gmail for unread emails, categorizes by priority, notifies only when needed.
"""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
import json

# Configuration
EMAIL = "edlmairfridolin@gmail.com"
APP_PASSWORD = "uwwf tlao blzj iecl"
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# Priority keywords
HIGH_PRIORITY_KEYWORDS = [
    'payment', 'invoice', 'bill', 'subscription', 'expired', 'expire', 'overdue',
    'deadline', 'urgent', 'failed', 'declined', 'rejected', 'action required',
    'verify', 'confirmation required', 'security alert', 'suspicious', 'unusual activity',
    'password reset', 'account locked', 'suspended', 'refund', 'charge'
]

MEDIUM_PRIORITY_KEYWORDS = [
    'business', 'client', 'customer', 'meeting', 'appointment', 'proposal', 'contract',
    'quote', 'inquiry', 'partnership', 'collaboration', 'opportunity', 'interview',
    'job', 'application', 'offer', 'project', 'consultation', 'contact form'
]

LOW_PRIORITY_KEYWORDS = [
    'newsletter', 'digest', 'weekly', 'monthly', 'update', 'announcement',
    'promotion', 'sale', 'discount', 'marketing', 'unsubscribe', 'no-reply',
    'notification', 'automated', 'noreply', 'donotreply', 'info@', 'support@'
]

SPAM_KEYWORDS = [
    'viagra', 'cialis', 'lottery', 'winner', 'million dollars', 'inheritance',
    'prince', 'nigerian', 'crypto investment', 'double your money', 'hot singles',
    'lose weight fast', 'work from home', 'make money fast', 'urgent: claim',
    'click here now', 'act now', 'limited time', 'congratulations you won'
]

def decode_email_header(header_value):
    """Decode email header to string."""
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result += part.decode(charset or 'utf-8', errors='ignore')
            except:
                result += part.decode('utf-8', errors='ignore')
        else:
            result += part
    return result

def extract_sender(from_header):
    """Extract sender name and email from From header."""
    if not from_header:
        return "Unknown"
    # Remove email address, keep name only
    match = re.match(r'"?([^"]+)"?\s*<', from_header)
    if match:
        return match.group(1).strip()
    # If no name, return email without < >
    match = re.match(r'<([^>]+)>', from_header)
    if match:
        return match.group(1)
    return from_header[:50]

def categorize_email(subject, sender, body_preview=""):
    """
    Categorize email by priority.
    Returns: ('HIGH'|'MEDIUM'|'LOW'|'SPAM', reason)
    """
    text = f"{subject} {sender} {body_preview}".lower()
    
    # Check for spam first
    for keyword in SPAM_KEYWORDS:
        if keyword in text:
            return ('SPAM', f"Spam keyword: {keyword}")
    
    # Check high priority
    for keyword in HIGH_PRIORITY_KEYWORDS:
        if keyword in text:
            return ('HIGH', f"High priority keyword: {keyword}")
    
    # Check medium priority
    for keyword in MEDIUM_PRIORITY_KEYWORDS:
        if keyword in text:
            return ('MEDIUM', f"Business keyword: {keyword}")
    
    # Check low priority
    for keyword in LOW_PRIORITY_KEYWORDS:
        if keyword in text:
            return ('LOW', f"Newsletter/notification keyword: {keyword}")
    
    # Check sender patterns for newsletters
    if any(x in sender.lower() for x in ['noreply', 'no-reply', 'donotreply', 'info@', 'newsletter']):
        return ('LOW', "No-reply sender")
    
    # Default to medium for unknown
    return ('MEDIUM', "Default - requires review")

def connect_and_fetch():
    """Connect to Gmail IMAP and fetch unread emails."""
    emails = []
    
    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL, APP_PASSWORD)
        mail.select('inbox')
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != 'OK' or not messages[0]:
            return []
        
        email_ids = messages[0].split()[:100]  # Max 100 emails
        
        for e_id in email_ids:
            try:
                # Fetch headers only first (fast)
                status, msg_data = mail.fetch(e_id, '(BODY.PEEK[HEADER])')
                if status != 'OK':
                    continue
                
                # Parse email
                msg = email.message_from_bytes(msg_data[0][1])
                subject = decode_email_header(msg.get('Subject', ''))
                sender = extract_sender(msg.get('From', ''))
                date = msg.get('Date', '')
                
                # Get a preview of body for better categorization
                body_preview = ""
                try:
                    status_body, body_data = mail.fetch(e_id, '(BODY.PEEK[TEXT]<0.1024>)')
                    if status_body == 'OK' and body_data[0]:
                        body_preview = body_data[0][1].decode('utf-8', errors='ignore')[:500]
                except:
                    pass
                
                priority, reason = categorize_email(subject, sender, body_preview)
                
                emails.append({
                    'id': e_id.decode(),
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'priority': priority,
                    'reason': reason
                })
                
            except Exception as e:
                continue
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"IMAP Error: {e}")
        return []
    
    return emails

def generate_summary(emails):
    """Generate a summary of processed emails."""
    if not emails:
        return {
            'total': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'spam': 0,
            'notify': False,
            'high_emails': [],
            'medium_emails': [],
            'message': "No new emails"
        }
    
    high = [e for e in emails if e['priority'] == 'HIGH']
    medium = [e for e in emails if e['priority'] == 'MEDIUM']
    low = [e for e in emails if e['priority'] == 'LOW']
    spam = [e for e in emails if e['priority'] == 'SPAM']
    
    # Notify if HIGH priority found
    notify = len(high) > 0
    
    return {
        'total': len(emails),
        'high': len(high),
        'medium': len(medium),
        'low': len(low),
        'spam': len(spam),
        'notify': notify,
        'high_emails': high,
        'medium_emails': medium,
        'message': f"New: {len(emails)} | 🔴: {len(high)} | 🟡: {len(medium)} | 🟢: {len(low)}"
    }

def main():
    print("🔍 Smart Gmail Automation v3 - Starting...")
    print(f"⏰ {datetime.now().strftime('%H:%M')}")
    print("-" * 50)
    
    # Fetch emails
    emails = connect_and_fetch()
    summary = generate_summary(emails)
    
    print(f"📊 {summary['message']}")
    
    if summary['total'] == 0:
        print("\n✅ No new emails. Silent mode - no notification sent.")
        return summary
    
    # Show breakdown
    if summary['spam'] > 0:
        print(f"🗑️  Auto-archive (spam): {summary['spam']}")
    
    if summary['high'] > 0:
        print(f"\n🔴 HIGH PRIORITY ({summary['high']}):")
        for e in summary['high_emails'][:5]:
            print(f"  • {e['sender']} - {e['subject'][:50]}")
    
    if summary['medium'] > 0:
        print(f"\n🟡 MEDIUM PRIORITY ({summary['medium']}):")
        for e in summary['medium_emails'][:3]:
            print(f"  • {e['sender']} - {e['subject'][:50]}")
    
    if summary['low'] > 0:
        print(f"\n🟢 LOW PRIORITY ({summary['low']}) - processed silently")
    
    # Determine if we should notify
    if summary['notify']:
        print("\n📱 TELEGRAM NOTIFICATION REQUIRED")
        print("Reason: High priority emails detected")
    elif summary['total'] > 0 and summary['high'] == 0:
        print("\n🔇 SILENT MODE - No high priority items")
        print("Only low/medium priority emails - no notification needed")
    
    print("-" * 50)
    print("✅ Automation complete")
    
    return summary

if __name__ == "__main__":
    result = main()
    # Output JSON for potential Telegram notification
    print("\nJSON_RESULT:" + json.dumps(result, default=str))
