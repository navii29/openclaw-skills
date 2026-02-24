#!/usr/bin/env python3
"""
AK Holding Auto-Reply Monitor
Checks Gmail and IONOS for unread emails from AK Holding and auto-replies with Calendly link
"""

import imaplib
import smtplib
import ssl
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime

# Credentials
GMAIL_USER = "edlmairfridolin@gmail.com"
GMAIL_PASS = "uwwf tlao blzj iecl"

IONOS_USER = "kontakt@navii-automation.de"
IONOS_PASS = "Billiondollar17"

# Target sender domains
TARGET_SENDERS = ["kara@ak-holding-gmbh.de", "ak-holding-gmbh.de"]

# Reply template
REPLY_TEMPLATE = """Hi Kara,

danke für deine Antwort!

Buche hier einen Termin: https://calendly.com/kontakt-navii-automation/new-meeting

Beste Grüße
Fridolin
Navii Automation
https://navii-automation.de
"""

def decode_subject(subject):
    """Decode email subject"""
    if subject is None:
        return ""
    decoded_parts = decode_header(subject)
    subject_parts = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                subject_parts.append(part.decode(charset or 'utf-8', errors='replace'))
            except:
                subject_parts.append(part.decode('utf-8', errors='replace'))
        else:
            subject_parts.append(part)
    return ''.join(subject_parts)

def get_sender_email(msg):
    """Extract sender email from message"""
    from_header = msg.get('From', '')
    # Extract email from "Name <email>" format
    if '<' in from_header and '>' in from_header:
        return from_header.split('<')[1].split('>')[0].lower()
    return from_header.lower().strip()

def is_target_sender(sender):
    """Check if sender matches target domains"""
    sender = sender.lower()
    return any(target in sender for target in TARGET_SENDERS)

def send_reply_via_ionos(to_email, subject, original_msg_id=None):
    """Send auto-reply via IONOS SMTP"""
    msg = MIMEMultipart()
    msg['From'] = IONOS_USER
    msg['To'] = to_email
    msg['Subject'] = f"Re: {subject}"
    if original_msg_id:
        msg['In-Reply-To'] = original_msg_id
        msg['References'] = original_msg_id
    
    msg.attach(MIMEText(REPLY_TEMPLATE, 'plain', 'utf-8'))
    
    context = ssl.create_default_context()
    with smtplib.SMTP('smtp.ionos.de', 587) as server:
        server.starttls(context=context)
        server.login(IONOS_USER, IONOS_PASS)
        server.send_message(msg)
    
    return True

def check_and_reply_gmail():
    """Check Gmail for unread emails from AK Holding"""
    results = []
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select('inbox')
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK' or not messages[0]:
            return []
        
        message_ids = messages[0].split()
        
        for msg_id in message_ids:
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            sender = get_sender_email(msg)
            
            if is_target_sender(sender):
                subject = decode_subject(msg.get('Subject', 'No Subject'))
                original_msg_id = msg.get('Message-ID')
                
                # Send reply via IONOS
                send_reply_via_ionos(sender, subject, original_msg_id)
                
                # Mark as read
                mail.store(msg_id, '+FLAGS', '\\Seen')
                
                results.append({
                    'account': 'Gmail',
                    'from': sender,
                    'subject': subject,
                    'action': 'Replied via IONOS + marked read'
                })
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        results.append({'account': 'Gmail', 'error': str(e)})
    
    return results

def check_and_reply_ionos():
    """Check IONOS for unread emails from AK Holding"""
    results = []
    try:
        mail = imaplib.IMAP4_SSL('imap.ionos.de')
        mail.login(IONOS_USER, IONOS_PASS)
        mail.select('inbox')
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK' or not messages[0]:
            return []
        
        message_ids = messages[0].split()
        
        for msg_id in message_ids:
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            sender = get_sender_email(msg)
            
            if is_target_sender(sender):
                subject = decode_subject(msg.get('Subject', 'No Subject'))
                original_msg_id = msg.get('Message-ID')
                
                # Send reply via IONOS
                send_reply_via_ionos(sender, subject, original_msg_id)
                
                # Mark as read
                mail.store(msg_id, '+FLAGS', '\\Seen')
                
                results.append({
                    'account': 'IONOS',
                    'from': sender,
                    'subject': subject,
                    'action': 'Replied + marked read'
                })
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        results.append({'account': 'IONOS', 'error': str(e)})
    
    return results

if __name__ == "__main__":
    print(f"AK Holding Auto-Reply Monitor")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    all_results = []
    
    # Check both accounts
    all_results.extend(check_and_reply_gmail())
    all_results.extend(check_and_reply_ionos())
    
    if not all_results:
        print("No new unread emails from AK Holding found.")
    else:
        for result in all_results:
            if 'error' in result:
                print(f"❌ ERROR [{result['account']}]: {result['error']}")
            else:
                print(f"✅ [{result['account']}] From: {result['from']}")
                print(f"   Subject: {result['subject']}")
                print(f"   Action: {result['action']}")
                print()
    
    print("-" * 50)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
