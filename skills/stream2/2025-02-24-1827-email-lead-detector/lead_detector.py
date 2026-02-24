#!/usr/bin/env python3
"""
Smart Email Lead Detector
Monitors Gmail inbox for potential customer leads using keyword scoring.
Sends Telegram alerts for high-value leads (score >= 7).
"""

import imaplib
import email
from email.header import decode_header
import re
import json
import os
from datetime import datetime, timedelta
import sys

# Add workspace to path for telegram skill
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills')

# Configuration
GMAIL_USER = "edlmairfridolin@gmail.com"
GMAIL_APP_PASSWORD = "uwwf tlao blzj iecl"
TELEGRAM_BOT_TOKEN = "8294286642:AAFKb09yfYMA5G4xrrr0yz0RCnHaph7IpBw"
TELEGRAM_CHAT_ID = "6599716126"

STATE_FILE = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1827-email-lead-detector/lead_state.json")

def load_state():
    """Load processed email IDs to avoid duplicates"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"processed_ids": [], "leads_found": 0}

def save_state(state):
    """Save processed email IDs"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def decode_subject(subject):
    """Decode email subject"""
    if subject:
        decoded = decode_header(subject)
        subject = ""
        for part, charset in decoded:
            if isinstance(part, bytes):
                subject += part.decode(charset or 'utf-8', errors='replace')
            else:
                subject += part
    return subject or "(No Subject)"

def extract_body(msg):
    """Extract email body"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        except:
            pass
    return body

# Lead scoring keywords
HIGH_VALUE_KEYWORDS = {
    'interesse': 2, 'angebot': 3, 'preis': 2, 'kosten': 2, 'budget': 3,
    'termin': 3, 'besprechung': 3, 'demo': 4, 'beratung': 3,
    'automation': 2, 'automatisierung': 2, 'workflow': 2, 'crm': 2,
    'sofort': 2, 'dringend': 3, 'wichtig': 2, 'projekt': 2,
    'zusammenarbeit': 3, 'partnerschaft': 3, 'einrichtung': 2,
    'implementierung': 3, 'integration': 2, 'ki': 2, 'ai': 2,
    'künstliche intelligenz': 3, 'chatbot': 2, 'telegram': 1,
    'email automation': 3, 'n8n': 2, 'make': 2, 'zapier': 2
}

NEGATIVE_KEYWORDS = {
    'newsletter': -2, 'unsubscribe': -5, 'abmelden': -5, 
    'werbung': -3, 'advertisement': -3, 'spam': -5,
    'no reply': -3, 'noreply': -3, 'do not reply': -3
}

def score_lead(subject, body, sender):
    """Score lead potential from 1-10"""
    score = 5  # Base score
    text = f"{subject} {body}".lower()
    
    # Check high-value keywords
    for keyword, points in HIGH_VALUE_KEYWORDS.items():
        if keyword in text:
            score += points
    
    # Check negative keywords
    for keyword, points in NEGATIVE_KEYWORDS.items():
        if keyword in text:
            score += points
    
    # Bonus for business domains
    business_domains = ['@company', '@gmbh', '@ag', '@ug', '@gmail', '@outlook']
    if any(domain in sender.lower() for domain in business_domains):
        score += 1
    
    # Bonus for direct questions
    question_words = ['?', 'wie', 'was', 'kann', 'können', 'welche', 'welcher']
    if any(q in text for q in question_words):
        score += 1
    
    return max(1, min(10, score))

def get_lead_emoji(score):
    """Get emoji based on lead score"""
    if score >= 8:
        return "🔥"
    elif score >= 6:
        return "⭐"
    elif score >= 4:
        return "📧"
    else:
        return "💤"

def send_telegram_alert(subject, sender, score, preview):
    """Send high-value lead alert to Telegram"""
    try:
        import urllib.request
        import urllib.parse
        
        emoji = get_lead_emoji(score)
        message = f"""{emoji} *NEUER LEAD ERKANNT!*

*Score:* {score}/10
*Von:* `{sender}`
*Betreff:* {subject[:100]}{'...' if len(subject) > 100 else ''}

*Preview:*
{preview[:200]}{'...' if len(preview) > 200 else ''}

⏰ {datetime.now().strftime('%H:%M %d.%m.%Y')}"""
        
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
        print(f"Telegram send failed: {e}")
        return False

def check_emails():
    """Main function to check emails and detect leads"""
    state = load_state()
    new_leads = []
    
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("inbox")
        
        # Search for unread emails from last 24h
        date_since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'(UNSEEN SINCE "{date_since}")')
        
        email_ids = messages[0].split()
        print(f"📧 Found {len(email_ids)} unread emails")
        
        for email_id in email_ids:
            email_id_str = email_id.decode()
            
            # Skip if already processed
            if email_id_str in state.get("processed_ids", []):
                continue
            
            # Fetch email
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract info
            subject = decode_subject(msg["Subject"])
            sender = msg.get("From", "Unknown")
            body = extract_body(msg)
            
            # Score the lead
            score = score_lead(subject, body, sender)
            
            # Store in state
            state["processed_ids"].append(email_id_str)
            
            # If high-value lead, send alert
            if score >= 7:
                state["leads_found"] += 1
                new_leads.append({
                    "sender": sender,
                    "subject": subject,
                    "score": score,
                    "time": datetime.now().isoformat()
                })
                
                send_telegram_alert(subject, sender, score, body)
                print(f"🔥 High-value lead sent! Score: {score} | Subject: {subject[:50]}")
            else:
                print(f"💤 Low-value lead ignored. Score: {score} | Subject: {subject[:50]}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error checking emails: {e}")
    
    # Save state
    save_state(state)
    
    return new_leads

if __name__ == "__main__":
    print(f"\n🤖 Smart Email Lead Detector - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    leads = check_emails()
    print(f"\n✅ Done! Found {len(leads)} high-value leads.")
    print(f"📊 Total leads found so far: {load_state().get('leads_found', 0)}")
