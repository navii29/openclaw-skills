#!/usr/bin/env python3
"""
Gmail Organizer - Clean up and organize inbox
"""

import imaplib
import email
from email.header import decode_header

EMAIL = "edlmairfridolin@gmail.com"
PASSWORD = "uwwf tlao blzj iecl"
IMAP_SERVER = "imap.gmail.com"

def connect_gmail():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    return mail

def create_label(mail, label_name):
    """Create a Gmail label if it doesn't exist"""
    try:
        # Gmail uses UTF-7 encoding for labels with special chars
        result = mail.create(label_name)
        print(f"  ✅ Label erstellt: {label_name}")
        return True
    except Exception as e:
        if "ALREADYEXISTS" in str(e):
            print(f"  ℹ️ Label existiert bereits: {label_name}")
            return True
        print(f"  ⚠️ Fehler bei {label_name}: {e}")
        return False

def archive_old_emails(mail, days=30):
    """Archive emails older than X days (not from important senders)"""
    mail.select("inbox")
    
    # Search for old emails using date format
    from datetime import datetime, timedelta
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
    _, messages = mail.search(None, f"(BEFORE {cutoff_date})")
    email_ids = messages[0].split()
    
    protected_senders = ['ak-holding', 'navii', 'muniqo', 'calendly']
    archived = 0
    skipped = 0
    
    print(f"\n📦 ARCHIVIERUNG ({len(email_ids)} alte E-Mails gefunden):")
    
    for email_id in email_ids[-50:]:  # Process last 50 old ones
        try:
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    from_addr = msg.get("From", "").lower()
                    subject = msg.get("Subject", "").lower()
                    
                    # Skip protected senders
                    if any(p in from_addr for p in protected_senders):
                        skipped += 1
                        continue
                    
                    # Skip unread emails
                    flags = mail.fetch(email_id, "(FLAGS)")[1][0].decode()
                    if "\\Seen" not in flags:
                        skipped += 1
                        continue
                    
                    # Archive: remove from Inbox label
                    mail.store(email_id, '-X-GM-LABELS', '\\Inbox')
                    archived += 1
                    
        except Exception as e:
            print(f"  Fehler bei E-Mail {email_id}: {e}")
    
    print(f"  ✅ Archiviert: {archived}")
    print(f"  🚫 Übersprungen (geschützt/ungelesen): {skipped}")

def organize_current_emails(mail):
    """Apply labels to current inbox emails"""
    mail.select("inbox")
    
    print("\n🏷️ E-MAILS KATEGORISIEREN:")
    
    # Label rules
    rules = [
        ('!AK-Holding', 'FROM', 'ak-holding-gmbh.de'),
        ('!Agentur', 'FROM', 'navii-automation.de'),
        ('Newsletter', 'FROM', ['newsletter', 'mailing', 'no-reply', 'noreply']),
        ('Einkauf', 'FROM', ['amazon', 'ebay', 'paypal', 'shopify', 'zalando']),
        ('Finanzen', 'FROM', ['bank', 'sparkasse', 'comdirect', 'coinbase', 'crypto']),
        ('Social', 'FROM', ['linkedin', 'xing', 'facebook', 'twitter', 'instagram']),
    ]
    
    labeled = defaultdict(int)
    
    _, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()
    
    for email_id in email_ids:
        try:
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    from_addr = msg.get("From", "").lower()
                    
                    for label, field, patterns in rules:
                        if isinstance(patterns, str):
                            patterns = [patterns]
                        
                        if any(p in from_addr for p in patterns):
                            mail.store(email_id, '+X-GM-LABELS', label)
                            labeled[label] += 1
                            break
                            
        except Exception as e:
            pass
    
    for label, count in sorted(labeled.items(), key=lambda x: -x[1]):
        print(f"  ✅ {label}: {count} E-Mails")
    
    if not labeled:
        print("  ℹ️ Keine passenden E-Mails zum Labeln gefunden")

def main():
    print("🧹 GMAIL AUFRÄUM-AKTION")
    print("=" * 40)
    
    mail = connect_gmail()
    
    # Step 1: Create labels
    print("\n📁 LABELS ERSTELLEN:")
    labels = ['!AK-Holding', '!Agentur', 'Newsletter', 'Einkauf', 'Finanzen', 'Social', 'Archiv']
    for label in labels:
        create_label(mail, label)
    
    # Step 2: Archive old emails (skip protected ones)
    archive_old_emails(mail, days=14)  # Archive emails older than 14 days
    
    # Step 3: Organize current emails
    organize_current_emails(mail)
    
    mail.close()
    mail.logout()
    
    print("\n" + "=" * 40)
    print("✅ AUFRÄUMEN ABGESCHLOSSEN!")
    print("\n📋 NÄCHSTE SCHRITTE:")
    print("1. Gmail-Web öffnen und Labels prüfen")
    print("2. Filter einrichten: Einstellungen → Filter und gesperrte Adressen")
    print("3. 'All Mail' für archivierte E-Mails durchsuchen")

if __name__ == "__main__":
    from collections import defaultdict
    main()
