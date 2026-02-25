#!/usr/bin/env python3
"""
Email zu Slack Support-Tickets
Monitor support emails and create Slack tickets automatically.
"""

import imaplib
import email
import re
import json
import requests
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
from email.header import decode_header


@dataclass
class SupportTicket:
    """Represents a support ticket from email."""
    ticket_id: str
    sender_name: str
    sender_email: str
    subject: str
    body: str
    timestamp: datetime
    priority: str
    category: str
    keywords: List[str]
    
    @property
    def summary(self) -> str:
        """Short summary for notifications."""
        return f"{self.subject[:50]}..." if len(self.subject) > 50 else self.subject


class EmailMonitor:
    """Monitor IMAP mailbox for support emails."""
    
    # Priority keywords (German)
    PRIORITY_KEYWORDS = {
        'critical': ['dringend', 'kritisch', 'ausfall', 'fehler', 'nicht funktioniert', 'sofort', 'wichtig'],
        'high': ['problem', 'hilfe', 'defekt', 'kaputt', 'error', 'bug', 'urgent'],
        'medium': ['frage', 'anfrage', 'support', 'hilfestellung'],
        'low': ['feedback', 'vorschlag', 'danke', 'lob']
    }
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        'technical': ['login', 'fehler', 'bug', 'defekt', 'technisch', 'problem'],
        'billing': ['rechnung', 'zahlung', 'bezahlen', 'mahnung', 'billing'],
        'sales': ['angebot', 'preis', 'kosten', 'kaufen', 'bestellen'],
        'general': ['frage', 'information', 'allgemein']
    }
    
    def __init__(self, imap_server: str, email_user: str, email_pass: str, 
                 support_address: Optional[str] = None):
        self.imap_server = imap_server
        self.email_user = email_user
        self.email_pass = email_pass
        self.support_address = support_address or email_user
        self.seen_uids: set = set()
    
    def connect(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server."""
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.email_user, self.email_pass)
        return mail
    
    def decode_header_value(self, value: str) -> str:
        """Decode email header value."""
        if not value:
            return ""
        decoded = decode_header(value)[0]
        if isinstance(decoded[0], bytes):
            return decoded[0].decode(decoded[1] or 'utf-8', errors='ignore')
        return str(decoded[0])
    
    def extract_body(self, msg) -> str:
        """Extract text body from email."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='ignore')
            except:
                pass
        return body[:2000]  # Limit length
    
    def analyze_priority(self, subject: str, body: str) -> tuple:
        """Analyze email priority and category."""
        text = f"{subject} {body}".lower()
        
        # Check priority
        priority = 'medium'
        priority_keywords = []
        
        for level, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    if level == 'critical':
                        priority = 'critical'
                        priority_keywords.append(keyword)
                    elif level == 'high' and priority not in ['critical']:
                        priority = 'high'
                        priority_keywords.append(keyword)
                    elif level == 'medium' and priority not in ['critical', 'high']:
                        priority = 'medium'
        
        # Check category
        category = 'general'
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    category = cat
                    break
            if category != 'general':
                break
        
        return priority, category, priority_keywords
    
    def fetch_new_emails(self, max_emails: int = 10) -> List[SupportTicket]:
        """Fetch new support emails."""
        tickets = []
        
        try:
            mail = self.connect()
            mail.select('inbox')
            
            # Search for unread emails
            _, search_data = mail.search(None, 'UNSEEN')
            email_ids = search_data[0].split()[-max_emails:]
            
            for e_id in email_ids:
                if e_id in self.seen_uids:
                    continue
                
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract info
                subject = self.decode_header_value(msg.get('Subject', ''))
                sender = self.decode_header_value(msg.get('From', ''))
                body = self.extract_body(msg)
                
                # Parse sender
                email_match = re.search(r'<?([^@>\s]+@[^@>\s]+)>?', sender)
                sender_email = email_match.group(1) if email_match else sender
                sender_name = re.sub(r'<[^\u003e]+>', '', sender).strip() or sender_email
                
                # Analyze priority
                priority, category, keywords = self.analyze_priority(subject, body)
                
                # Create ticket
                ticket = SupportTicket(
                    ticket_id=f"TKT-{datetime.now().strftime('%Y%m%d')}-{e_id.decode()[-4:]}",
                    sender_name=sender_name,
                    sender_email=sender_email,
                    subject=subject,
                    body=body,
                    timestamp=datetime.now(),
                    priority=priority,
                    category=category,
                    keywords=keywords
                )
                
                tickets.append(ticket)
                self.seen_uids.add(e_id)
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
        
        return tickets


class SlackNotifier:
    """Send ticket notifications to Slack."""
    
    # Priority emoji mapping
    PRIORITY_ICONS = {
        'critical': '🚨',
        'high': '🔥',
        'medium': '📋',
        'low': '💬'
    }
    
    CATEGORY_ICONS = {
        'technical': '🔧',
        'billing': '💰',
        'sales': '💼',
        'general': '📧'
    }
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def format_ticket(self, ticket: SupportTicket) -> Dict:
        """Format ticket for Slack message."""
        priority_icon = self.PRIORITY_ICONS.get(ticket.priority, '📋')
        category_icon = self.CATEGORY_ICONS.get(ticket.category, '📧')
        
        body_preview = ticket.body[:300] + "..." if len(ticket.body) > 300 else ticket.body
        
        # Clean body for Slack
        body_preview = body_preview.replace('\r', '').replace('\n\n', '\n')
        
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{priority_icon} NEUES TICKET: {ticket.ticket_id}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Von:*\n{ticket.sender_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Email:*\n{ticket.sender_email}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Kategorie:*\n{category_icon} {ticket.category.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Priorität:*\n{priority_icon} {ticket.priority.upper()}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Betreff:* {ticket.subject}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Nachricht:*\n```{body_preview}```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"⏰ {ticket.timestamp.strftime('%d.%m.%Y %H:%M')} | 🔴 Offen"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Übernehmen",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": f"claim_{ticket.ticket_id}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "➡️ Weiterleiten",
                                "emoji": True
                            },
                            "value": f"escalate_{ticket.ticket_id}"
                        }
                    ]
                }
            ]
        }
    
    def send_ticket(self, ticket: SupportTicket) -> bool:
        """Send ticket to Slack."""
        payload = self.format_ticket(ticket)
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            success = response.status_code == 200
            if success:
                print(f"   ✅ Slack sent: {ticket.ticket_id}")
            else:
                print(f"   ❌ Slack failed: {response.status_code}")
            return success
        except Exception as e:
            print(f"   ❌ Slack error: {e}")
            return False


class EmailSlackIntegration:
    """Main integration orchestrator."""
    
    def __init__(self, imap_server: str, email_user: str, email_pass: str,
                 slack_webhook: str, support_address: Optional[str] = None):
        self.email_monitor = EmailMonitor(imap_server, email_user, email_pass, support_address)
        self.slack = SlackNotifier(slack_webhook)
    
    def run(self, max_emails: int = 10) -> Dict:
        """Run one cycle of email check and Slack notification."""
        print("🔍 Checking for new support emails...")
        
        tickets = self.email_monitor.fetch_new_emails(max_emails)
        
        if not tickets:
            print("   No new emails")
            return {"checked": 0, "sent": 0}
        
        print(f"   Found {len(tickets)} new ticket(s)")
        
        sent = 0
        for ticket in tickets:
            print(f"\n🎫 {ticket.ticket_id}: {ticket.subject[:50]}")
            print(f"   From: {ticket.sender_email}")
            print(f"   Priority: {ticket.priority} | Category: {ticket.category}")
            
            if self.slack.send_ticket(ticket):
                sent += 1
        
        return {"checked": len(tickets), "sent": sent}


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email zu Slack Support-Tickets')
    parser.add_argument('--imap-server', required=True, help='IMAP server (e.g., imap.gmail.com)')
    parser.add_argument('--email', required=True, help='Email address')
    parser.add_argument('--password', required=True, help='Email password')
    parser.add_argument('--slack-webhook', required=True, help='Slack Webhook URL')
    parser.add_argument('--support-address', help='Support email address (if different)')
    parser.add_argument('--max', type=int, default=10, help='Max emails to process')
    parser.add_argument('--interval', type=int, help='Run continuously with interval (seconds)')
    
    args = parser.parse_args()
    
    integration = EmailSlackIntegration(
        args.imap_server,
        args.email,
        args.password,
        args.slack_webhook,
        args.support_address
    )
    
    if args.interval:
        import time
        print(f"🤖 Running continuously every {args.interval}s\n")
        while True:
            result = integration.run(args.max)
            print(f"\n⏳ Sleeping {args.interval}s...\n")
            time.sleep(args.interval)
    else:
        result = integration.run(args.max)
        print(f"\n✅ Done: {result['sent']}/{result['checked']} sent to Slack")


if __name__ == "__main__":
    main()
