#!/usr/bin/env python3
"""
Delete specific email from AK Holding
"""

import imaplib
import email

EMAIL = "edlmairfridolin@gmail.com"
PASSWORD = "uwwf tlao blzj iecl"
IMAP_SERVER = "imap.gmail.com"

def connect_gmail():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    return mail

def delete_ak_holding_emails():
    mail = connect_gmail()
    
    # Check inbox
    for folder in ['inbox', '[Gmail]/All Mail']:
        mail.select(folder)
        
        # Search for emails from AK Holding
        _, messages = mail.search(None, 'FROM', 'ak-holding-gmbh.de')
        email_ids = messages[0].split()
        
        print(f"📁 {folder}: {len(email_ids)} AK Holding E-Mail(s) gefunden")
        
        for email_id in email_ids:
            # Get email details
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = msg.get("Subject", "(Kein Betreff)")
                    print(f"  🗑️ Lösche: {subject[:50]}")
            
            # Delete email (move to trash)
            mail.store(email_id, '+X-GM-LABELS', '\\Trash')
            print(f"     → In den Papierkorb verschoben")
    
    mail.close()
    mail.logout()
    print("\n✅ AK Holding E-Mail(s) gelöscht (im Papierkorb)")

if __name__ == "__main__":
    print("🗑️ AK Holding Test-E-Mail löschen\n")
    delete_ak_holding_emails()
