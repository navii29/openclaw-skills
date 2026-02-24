#!/usr/bin/env python3
"""
Remove AK Holding label from Gmail
"""

import imaplib

EMAIL = "edlmairfridolin@gmail.com"
PASSWORD = "uwwf tlao blzj iecl"
IMAP_SERVER = "imap.gmail.com"

def connect_gmail():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    return mail

def remove_label(label_name):
    mail = connect_gmail()
    try:
        # Delete the label
        result = mail.delete(label_name)
        print(f"✅ Label '{label_name}' gelöscht")
        return True
    except Exception as e:
        print(f"⚠️ Fehler beim Löschen: {e}")
        return False
    finally:
        mail.logout()

if __name__ == "__main__":
    print("🗑️ AK Holding Label entfernen\n")
    remove_label("!AK-Holding")
