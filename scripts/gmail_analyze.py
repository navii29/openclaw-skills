#!/usr/bin/env python3
"""
Gmail Inbox Analyzer & Organizer
Analyzes edlmairfridolin@gmail.com inbox and provides cleanup suggestions
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import re
from collections import Counter, defaultdict

# Gmail credentials
EMAIL = "edlmairfridolin@gmail.com"
PASSWORD = "uwwf tlao blzj iecl"
IMAP_SERVER = "imap.gmail.com"

def connect_gmail():
    """Connect to Gmail IMAP"""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    return mail

def get_email_content(msg):
    """Extract email content"""
    content = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                except:
                    pass
    else:
        try:
            content = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    return content[:500]  # First 500 chars

def analyze_inbox():
    """Analyze inbox and categorize emails"""
    mail = connect_gmail()
    mail.select("inbox")
    
    # Search for all emails
    _, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    
    print(f"📊 GESAMT: {len(email_ids)} E-Mails im Posteingang\n")
    
    # Categorization
    categories = defaultdict(list)
    unread_count = 0
    old_count = 0
    
    # Analyze last 100 emails (for speed)
    recent_ids = email_ids[-100:] if len(email_ids) > 100 else email_ids
    
    for email_id in recent_ids:
        _, msg_data = mail.fetch(email_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Extract info
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode('utf-8', errors='ignore')
                subject = subject or "(Kein Betreff)"
                
                from_addr = msg.get("From", "")
                date_str = msg.get("Date", "")
                
                # Check unread
                flags = mail.fetch(email_id, "(FLAGS)")[1][0].decode()
                is_unread = "\\Seen" not in flags
                
                # Categorize by sender domain
                domain_match = re.search(r'@([^>\s]+)', from_addr)
                domain = domain_match.group(1).lower() if domain_match else "unknown"
                
                # Simple categorization
                category = "sonstige"
                if any(x in domain for x in ['newsletter', 'mailing', 'campaign']):
                    category = "newsletter"
                elif any(x in domain for x in ['noreply', 'no-reply', 'notification']):
                    category = "benachrichtigungen"
                elif any(x in domain for x in ['shop', 'store', 'amazon', 'ebay', 'paypal']):
                    category = "einkauf"
                elif any(x in domain for x in ['bank', 'finance', 'crypto', 'coinbase']):
                    category = "finanzen"
                elif any(x in domain for x in ['social', 'facebook', 'linkedin', 'twitter', 'x.com']):
                    category = "social"
                elif any(x in from_addr.lower() for x in ['ak-holding', 'navii']):
                    category = "geschaeftlich"
                
                email_info = {
                    'id': email_id.decode(),
                    'subject': subject[:60],
                    'from': from_addr[:50],
                    'domain': domain,
                    'unread': is_unread
                }
                
                categories[category].append(email_info)
                if is_unread:
                    unread_count += 1
    
    mail.close()
    mail.logout()
    
    # Print analysis
    print("📁 KATEGORIEN:\n")
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        unread_in_cat = sum(1 for i in items if i['unread'])
        unread_marker = f" ({unread_in_cat} ungelesen)" if unread_in_cat > 0 else ""
        print(f"  {cat.upper()}: {len(items)} E-Mails{unread_marker}")
        for item in items[:3]:  # Show first 3
            unread_dot = "🔴" if item['unread'] else "  "
            print(f"    {unread_dot} {item['subject'][:45]}")
        if len(items) > 3:
            print(f"    ... und {len(items) - 3} weitere")
        print()
    
    print(f"📌 UNGELESEN: {unread_count}")
    print(f"📧 AKTUELL ANALYSIERT: {len(recent_ids)} (letzte E-Mails)")

if __name__ == "__main__":
    analyze_inbox()
