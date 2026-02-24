#!/usr/bin/env python3
"""
Inbox AI - Main Email Processor
Monitors inbox, categorizes, prioritizes, and auto-replies
"""
import os
import sys
import json
import time
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import ssl
import smtplib

# Load config from environment
CONFIG_FILE = os.path.expanduser("~/.openclaw/workspace/inbox-ai-config.env")

def load_config():
    """Load configuration from env file"""
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    return config

def connect_imap(config):
    """Connect to IMAP server"""
    imap = imaplib.IMAP4_SSL(config['IMAP_SERVER'], int(config.get('IMAP_PORT', 993)))
    imap.login(config['EMAIL_USERNAME'], config['EMAIL_PASSWORD'])
    return imap

def categorize_email(subject, body, sender):
    """
    Categorize email by type
    Returns: category, priority_score (0-1), requires_escalation
    """
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    # Spam detection
    spam_keywords = ['unsubscribe', 'werbung', 'newsletter', 'no-reply']
    if any(k in sender.lower() or k in subject_lower for k in spam_keywords):
        return 'spam', 0.0, False
    
    # Urgency indicators
    urgent_keywords = ['dringend', 'urgent', 'asap', 'sofort', 'wichtig', 'deadline']
    urgency_score = sum(1 for k in urgent_keywords if k in subject_lower or k in body_lower) / len(urgent_keywords)
    
    # Category detection
    if any(k in subject_lower for k in ['termin', 'meeting', 'calendly', 'buchung']):
        category = 'booking'
    elif any(k in subject_lower for k in ['support', 'hilfe', 'problem', 'fehler']):
        category = 'support'
    elif any(k in subject_lower for k in ['angebot', 'preis', 'kosten', 'angebot']):
        category = 'inquiry'
    elif any(k in subject_lower for k in ['rechnung', 'invoice', 'zahlung', 'payment']):
        category = 'billing'
    else:
        category = 'general'
    
    # Priority scoring (0-1)
    priority = min(0.3 + urgency_score * 0.7, 1.0)
    
    # Escalation rules
    requires_escalation = (
        urgency_score > 0.6 or  # High urgency
        'beschwerde' in body_lower or  # Complaint
        'klage' in body_lower or  # Legal
        len(body) > 3000  # Very complex
    )
    
    return category, priority, requires_escalation

def generate_summary(subject, body):
    """Generate TL;DR summary"""
    # Simple extraction - in production, this calls the AI model
    lines = body.strip().split('\n')
    # Get first substantial line
    for line in lines:
        line = line.strip()
        if len(line) > 20 and not line.startswith('>'):
            return line[:200] + ('...' if len(line) > 200 else '')
    return subject

def should_auto_reply(category, priority, requires_escalation, config):
    """Determine if we should auto-reply"""
    if not config.get('AUTO_REPLY_ENABLED', 'true').lower() == 'true':
        return False
    if requires_escalation:
        return False
    if category == 'spam':
        return False
    if priority > float(config.get('ESCALATION_THRESHOLD', 0.7)):
        return False
    return True

def generate_reply(category, subject, body, config):
    """Generate contextual auto-reply"""
    from_name = config.get('FROM_NAME', 'Your Team')
    
    templates = {
        'booking': f"""Hallo,

vielen Dank für Ihre Terminanfrage. Ich habe Ihre Nachricht erhalten und werde mich in Kürze mit verfügbaren Terminen bei Ihnen melden.

Alternativ können Sie direkt einen Termin buchen:
{config.get('CALENDLY_LINK', '[Calendly-Link einfügen]')}

Mit freundlichen Grüßen
{from_name}""",
        
        'inquiry': f"""Hallo,

vielen Dank für Ihr Interesse. Ich habe Ihre Anfrage erhalten und prüfe aktuell die Details. Sie erhalten innerhalb der nächsten 24 Stunden ein maßgeschneidertes Angebot.

Bei dringenden Fragen erreichen Sie mich auch telefonisch.

Mit freundlichen Grüßen
{from_name}""",
        
        'support': f"""Hallo,

vielen Dank für Ihre Nachricht. Ich habe Ihr Anliegen verstanden und arbeite daran.

Ich werde mich schnellstmöglich mit einer Lösung oder Rückfragen bei Ihnen melden.

Mit freundlichen Grüßen
{from_name}""",
        
        'general': f"""Hallo,

vielen Dank für Ihre E-Mail. Ich habe Ihre Nachricht erhalten und werde mich so schnell wie möglich bei Ihnen melden.

Mit freundlichen Grüßen
{from_name}"""
    }
    
    return templates.get(category, templates['general'])

def send_reply(to_email, subject, body, in_reply_to, config):
    """Send email reply via SMTP"""
    msg = MIMEMultipart()
    msg['From'] = f"{config.get('FROM_NAME')} <{config['EMAIL_USERNAME']}>"
    msg['To'] = to_email
    msg['Subject'] = f"Re: {subject}"
    msg['In-Reply-To'] = in_reply_to
    msg['References'] = in_reply_to
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    context = ssl.create_default_context()
    with smtplib.SMTP(config['SMTP_SERVER'], int(config.get('SMTP_PORT', 587))) as server:
        server.starttls(context=context)
        server.login(config['EMAIL_USERNAME'], config['EMAIL_PASSWORD'])
        server.send_message(msg)
    
    return True

def process_emails(mode='monitor'):
    """Main processing loop"""
    config = load_config()
    if not config:
        print(f"ERROR: Config not found at {CONFIG_FILE}")
        sys.exit(1)
    
    print(f"[{datetime.now()}] Inbox AI starting in {mode} mode...")
    
    try:
        imap = connect_imap(config)
        imap.select('INBOX')
        
        # Search for unread emails
        _, messages = imap.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        
        print(f"Found {len(email_ids)} unread emails")
        
        processed = []
        for email_id in email_ids:
            _, msg_data = imap.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract info
            subject = msg['subject'] or '(no subject)'
            sender = msg['from']
            msg_id = msg['message-id']
            
            # Get body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            # Categorize
            category, priority, requires_escalation = categorize_email(subject, body, sender)
            summary = generate_summary(subject, body)
            
            result = {
                'id': email_id.decode(),
                'from': sender,
                'subject': subject,
                'category': category,
                'priority': round(priority, 2),
                'escalation': requires_escalation,
                'summary': summary,
                'action': 'none'
            }
            
            # Determine action
            if mode == 'auto' and should_auto_reply(category, priority, requires_escalation, config):
                reply_body = generate_reply(category, subject, body, config)
                send_reply(sender, subject, reply_body, msg_id, config)
                result['action'] = 'auto_replied'
                print(f"✓ Auto-replied to: {subject[:50]}...")
            elif requires_escalation:
                result['action'] = 'escalated'
                print(f"⚠ Escalated: {subject[:50]}...")
            else:
                result['action'] = 'categorized'
                print(f"• Categorized: {subject[:50]}...")
            
            processed.append(result)
        
        imap.close()
        imap.logout()
        
        # Save processing log
        log_file = f"/tmp/inbox-ai-{datetime.now().strftime('%Y%m%d')}.json"
        with open(log_file, 'w') as f:
            json.dump(processed, f, indent=2)
        
        print(f"\nProcessed {len(processed)} emails. Log: {log_file}")
        return processed
        
    except Exception as e:
        print(f"ERROR: {e}")
        raise

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'monitor'
    process_emails(mode)
