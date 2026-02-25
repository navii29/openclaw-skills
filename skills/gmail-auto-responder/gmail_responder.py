#!/usr/bin/env python3
"""
Gmail Auto-Label + Smart Replies
Automatically classify and label emails, generate reply suggestions.
"""

import imaplib
import smtplib
import email
import re
import json
from email.mime.text import MIMEText
from email.header import decode_header
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os

class GmailAutoResponder:
    """Auto-classify and label Gmail messages."""
    
    # Email classification patterns (German-focused)
    CATEGORIES = {
        'rechnung': {
            'keywords': ['rechnung', 'invoice', 'zahlung', 'bezahlt', 'überweisung', 'mahnung'],
            'label': 'Rechnungen',
            'priority': 'high',
            'color': '#fb4c2f'
        },
        'angebot': {
            'keywords': ['angebot', 'kostenvoranschlag', 'preis', 'kosten', 'angebot anfordern'],
            'label': 'Angebote',
            'priority': 'high', 
            'color': '#16a766'
        },
        'support': {
            'keywords': ['problem', 'hilfe', 'fehler', 'defekt', 'kaputt', 'funktioniert nicht'],
            'label': 'Support',
            'priority': 'high',
            'color': '#ff9900'
        },
        'termin': {
            'keywords': ['termin', 'besprechung', 'meeting', 'call', 'telefonat', 'zoom'],
            'label': 'Termine',
            'priority': 'medium',
            'color': '#7986cb'
        },
        'bewerbung': {
            'keywords': ['bewerbung', 'lebenslauf', 'anschreiben', 'stelle', 'job'],
            'label': 'Bewerbungen',
            'priority': 'medium',
            'color': '#b39ddb'
        },
        'marketing': {
            'keywords': ['newsletter', 'werbung', 'aktion', 'rabatt', 'angebot', 'unsubscribe'],
            'label': 'Marketing',
            'priority': 'low',
            'color': '#616161'
        }
    }
    
    # Reply templates (German)
    TEMPLATES = {
        'rechnung': """Sehr geehrte Damen und Herren,

vielen Dank für Ihre Rechnung. Wir werden diese prüfen und zeitnah bearbeiten.

Bei Rückfragen melden wir uns bei Ihnen.

Mit freundlichen Grüßen
[Name]
""",
        'angebot': """Sehr geehrte Damen und Herren,

vielen Dank für Ihre Anfrage. Wir prüfen Ihr Anliegen und erstellen Ihnen zeitnah ein passendes Angebot.

Wir melden uns in Kürze bei Ihnen.

Mit freundlichen Grüßen
[Name]
""",
        'support': """Sehr geehrte Damen und Herren,

vielen Dank für Ihre Nachricht. Wir haben Ihr Anliegen erhalten und kümmern uns schnellstmöglich darum.

Wir melden uns zeitnah mit einer Lösung bei Ihnen.

Mit freundlichen Grüßen
[Name]
""",
        'termin': """Sehr geehrte Damen und Herren,

vielen Dank für Ihre Terminanfrage. Ich prüfe meinen Kalender und melde mich mit Terminvorschlägen bei Ihnen.

Mit freundlichen Grüßen
[Name]
""",
        'bewerbung': """Sehr geehrte/r [Name],

vielen Dank für Ihre Bewerbung. Wir haben Ihre Unterlagen erhalten und prüfen diese sorgfältig.

Wir melden uns in den nächsten Tagen bei Ihnen.

Mit freundlichen Grüßen
HR-Team
"""
    }
    
    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = "imap.gmail.com"
        self.smtp_server = "smtp.gmail.com"
        self.processed_ids = set()
    
    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail IMAP."""
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.email_address, self.app_password)
        return mail
    
    def decode_subject(self, subject: bytes) -> str:
        """Decode email subject."""
        if not subject:
            return "(No Subject)"
        decoded = decode_header(subject)[0]
        if isinstance(decoded[0], bytes):
            return decoded[0].decode(decoded[1] or 'utf-8', errors='ignore')
        return str(decoded[0])
    
    def decode_body(self, msg) -> str:
        """Extract text body from email."""
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
        return body.lower()
    
    def classify_email(self, subject: str, body: str, sender: str) -> Tuple[str, float]:
        """Classify email into category."""
        text = f"{subject.lower()} {body}"
        scores = {}
        
        for category, config in self.CATEGORIES.items():
            score = 0
            for keyword in config['keywords']:
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
                score += count
            if score > 0:
                scores[category] = score
        
        if not scores:
            return ('unbekannt', 0.0)
        
        best_category = max(scores, key=scores.get)
        return (best_category, scores[best_category])
    
    def create_draft_reply(self, original_msg, category: str) -> Optional[MIMEText]:
        """Create a draft reply based on template."""
        if category not in self.TEMPLATES:
            return None
        
        template = self.TEMPLATES[category]
        
        # Extract original sender
        from_addr = original_msg.get('From', '')
        
        # Create reply
        reply = MIMEText(template, 'plain', 'utf-8')
        reply['To'] = from_addr
        reply['From'] = self.email_address
        reply['Subject'] = f"Re: {self.decode_subject(original_msg.get('Subject', ''))}"
        reply['In-Reply-To'] = original_msg.get('Message-ID', '')
        reply['References'] = original_msg.get('Message-ID', '')
        
        return reply
    
    def process_unread_emails(self, max_emails: int = 10, create_drafts: bool = True) -> List[Dict]:
        """Process unread emails."""
        results = []
        
        try:
            mail = self.connect_imap()
            mail.select('inbox')
            
            # Search for unread emails
            _, search_data = mail.search(None, 'UNSEEN')
            email_ids = search_data[0].split()[-max_emails:]  # Get last N
            
            print(f"📧 Found {len(email_ids)} unread emails")
            
            for e_id in email_ids:
                if e_id in self.processed_ids:
                    continue
                    
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract info
                subject = self.decode_subject(msg.get('Subject', ''))
                body = self.decode_body(msg)
                sender = msg.get('From', '')
                
                # Classify
                category, confidence = self.classify_email(subject, body, sender)
                
                result = {
                    'id': e_id.decode(),
                    'subject': subject[:80],
                    'sender': sender[:50],
                    'category': category,
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"  📨 {subject[:50]}... → {category.upper()} ({confidence})")
                
                # Create draft if applicable
                if create_drafts and category in self.TEMPLATES:
                    draft = self.create_draft_reply(msg, category)
                    if draft:
                        # Save draft via IMAP
                        draft_bytes = draft.as_bytes()
                        mail.append('[Gmail]/Drafts', '\\Seen', imaplib.Time2Internaldate(datetime.now()), draft_bytes)
                        result['draft_created'] = True
                        print(f"     ✉️ Draft reply created")
                
                results.append(result)
                self.processed_ids.add(e_id)
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate processing report."""
        if not results:
            return "No emails processed."
        
        categories = {}
        for r in results:
            cat = r['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        report = f"""
📊 Email Processing Report
========================
Processed: {len(results)} emails
Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

By Category:
"""
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            report += f"  • {cat.upper()}: {count}\n"
        
        return report


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gmail Auto-Label + Smart Replies')
    parser.add_argument('--email', required=True, help='Gmail address')
    parser.add_argument('--password', required=True, help='Gmail App Password')
    parser.add_argument('--max', type=int, default=10, help='Max emails to process')
    parser.add_argument('--no-drafts', action='store_true', help='Skip draft creation')
    
    args = parser.parse_args()
    
    print("🚀 Starting Gmail Auto-Responder...\n")
    
    responder = GmailAutoResponder(args.email, args.password)
    results = responder.process_unread_emails(
        max_emails=args.max,
        create_drafts=not args.no_drafts
    )
    
    print("\n" + responder.generate_report(results))
    
    # Save results
    if results:
        output_file = f"email_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Report saved to {output_file}")


if __name__ == "__main__":
    main()
