#!/usr/bin/env python3
"""Smart Gmail Automation - Check and categorize emails"""
import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
import json

# Gmail credentials
EMAIL = "edlmairfridolin@gmail.com"
APP_PASSWORD = "uwwf tlao blzj iecl"
IMAP_SERVER = "imap.gmail.com"

# Priority keywords
URGENT_KEYWORDS = ['urgent', 'asap', 'immediately', 'deadline', 'due', 'overdue', 'important', 'action required']
HIGH_SENDERS = ['boss', 'manager', 'ceo', 'founder', 'client', 'customer']
ACTION_KEYWORDS = ['please review', 'need your input', 'confirm', 'approve', 'respond', 'reply needed']
NEWSLETTER_KEYWORDS = ['newsletter', 'unsubscribe', 'promotional', 'marketing', 'no-reply', 'noreply']

def connect_gmail():
    """Connect to Gmail IMAP"""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, APP_PASSWORD)
        return mail
    except Exception as e:
        return None, str(e)

def decode_email_header(header):
    """Decode email header"""
    if not header:
        return ""
    decoded, charset = decode_header(header)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(charset or 'utf-8', errors='ignore')
    return decoded

def get_email_body(msg):
    """Extract email body"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    return body[:2000]  # Limit body size

def categorize_email(subject, sender, body):
    """Categorize email by priority"""
    subject_lower = subject.lower()
    sender_lower = sender.lower()
    body_lower = body.lower()
    combined = f"{subject_lower} {body_lower}"
    
    # Check for newsletters/spam first
    for kw in NEWSLETTER_KEYWORDS:
        if kw in sender_lower or kw in subject_lower:
            return 'SPAM', None
    
    # Check for urgent/high priority
    for kw in URGENT_KEYWORDS:
        if kw in combined:
            return 'HIGH', 'urgent'
    
    for kw in ACTION_KEYWORDS:
        if kw in combined:
            return 'HIGH', 'action_required'
    
    # Check sender importance
    for s in HIGH_SENDERS:
        if s in sender_lower:
            return 'HIGH', 'important_sender'
    
    # Check for deadlines
    deadline_patterns = [r'\bby\s+\w+', r'deadline', r'due\s+date', r'\d{1,2}[./]\d{1,2}[./]\d{2,4}']
    for pattern in deadline_patterns:
        if re.search(pattern, combined):
            return 'HIGH', 'deadline'
    
    # Business/collaboration patterns
    business_keywords = ['meeting', 'project', 'proposal', 'collaboration', 'partnership', 'inquiry']
    for kw in business_keywords:
        if kw in combined:
            return 'MEDIUM', 'business'
    
    return 'LOW', 'general'

def extract_tldr(subject, body, priority):
    """Generate TL;DR summary"""
    # Simple extraction of key info
    tldr = subject[:80] if len(subject) <= 80 else subject[:77] + "..."
    
    # Look for action items
    action = None
    action_patterns = [
        r'(?:please|kindly)\s+(\w+.*?)[.\n]',
        r'(review|approve|confirm|respond|reply).*?by\s+([^\n]+)',
        r'(deadline|due)\s*:?\s*([^\n]+)',
    ]
    for pattern in action_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            action = match.group(0)[:60]
            break
    
    if not action and priority == 'HIGH':
        action = "⚠️ Action required"
    elif not action:
        action = "📖 For info"
    
    return tldr, action

def main():
    results = {
        'total': 0,
        'high': [],
        'medium': [],
        'low': [],
        'spam': [],
        'timestamp': datetime.now().strftime('%H:%M')
    }
    
    # Connect to Gmail
    mail = connect_gmail()
    if isinstance(mail, tuple):
        print(f"ERROR: Failed to connect - {mail[1]}")
        return json.dumps(results)
    
    try:
        mail.select('inbox')
        
        # Search for unread emails (limit to 300)
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != 'OK' or not messages[0]:
            results['message'] = "No new emails"
            return json.dumps(results)
        
        email_ids = messages[0].split()[-300:]  # Get last 300
        results['total'] = len(email_ids)
        
        for eid in reversed(email_ids):  # Newest first
            status, msg_data = mail.fetch(eid, '(RFC822)')
            
            if status != 'OK':
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = decode_email_header(msg['Subject'])
            sender = decode_email_header(msg['From'])
            date = msg['Date']
            
            # Extract sender email/name
            sender_match = re.search(r'<([^>]+)>', sender)
            sender_email = sender_match.group(1) if sender_match else sender
            sender_name = sender.split('<')[0].strip()[:30]
            
            body = get_email_body(msg)
            
            # Categorize
            priority, reason = categorize_email(subject, sender_email, body)
            tldr, action = extract_tldr(subject, body, priority)
            
            email_data = {
                'id': eid.decode(),
                'sender': sender_name or sender_email[:30],
                'subject': subject[:60],
                'tldr': tldr,
                'action': action,
                'reason': reason
            }
            
            if priority == 'HIGH':
                results['high'].append(email_data)
            elif priority == 'MEDIUM':
                results['medium'].append(email_data)
            elif priority == 'SPAM':
                results['spam'].append(email_data)
            else:
                results['low'].append(email_data)
            
            # Mark as seen
            mail.store(eid, '+FLAGS', '\\Seen')
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        results['error'] = str(e)
    
    return json.dumps(results, indent=2)

if __name__ == "__main__":
    print(main())
