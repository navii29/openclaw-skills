#!/usr/bin/env python3
"""
Gmail Organization System
Automates label creation and email categorization via IMAP
"""

import imaplib
import ssl
import email
from email.header import decode_header
from datetime import datetime, timezone
import re
import sys

# Configuration
EMAIL = "edlmairfridolin@gmail.com"
PASSWORD = "uwwf tlao blzj iecl"
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# Label definitions (using simpler ASCII names for compatibility)
LABELS_TO_CREATE = [
    "Action-Required",
    "Review",
    "Read-Later",
    "00-Action",
    "01-Review",
    "99-Archive",
    "Auto-Archived"
]

# Sender pattern matching rules
SENDER_PATTERNS = {
    'payment_subscription': [
        r'paypal', r'stripe', r'square', r'invoice', r'billing', r'payment',
        r'subscription', r'renewal', r'netflix', r'spotify', r'apple\.com',
        r'amazon\.de', r'amzn', r'google\.com', r'microsoft', r'adobe',
        r'rechnung', r'zahlung', r'abonnement', r'kündigung'
    ],
    'newsletters': [
        r'dailyom', r'linkedin', r'twitter', r'x\.com', r'facebook', r'meta',
        r'instagram', r'pinterest', r'medium', r'substack', r'newsletter',
        r'mailchimp', r'sendinblue', r'campaign', r'update', r'digest',
        r'weekly', r'monthly', r'blog', r'patreon'
    ],
    'orders_shipping': [
        r'order', r'bestellung', r'versand', r'shipment', r'tracking',
        r'delivery', r'lieferung', r'amazon', r'ebay', r'etsy', r'shopify',
        r'confirmation', r'bestätigung', r'receipt', r'quittung'
    ]
}

class GmailOrganizer:
    def __init__(self):
        self.mail = None
        self.stats = {
            'labels_created': [],
            'emails_archived_90plus': 0,
            'emails_archived_30_90': 0,
            'emails_labeled_7_30': 0,
            'smart_labeled_action': 0,
            'smart_labeled_review': 0,
            'smart_labeled_read_later': 0,
            'top_senders': {}
        }

    def connect(self):
        """Connect to Gmail IMAP"""
        print("📧 Connecting to Gmail IMAP...")
        context = ssl.create_default_context()
        self.mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, ssl_context=context)
        self.mail.login(EMAIL, PASSWORD)
        print("✅ Connected successfully!")
        return True

    def disconnect(self):
        """Disconnect from Gmail"""
        if self.mail:
            try:
                self.mail.close()
            except:
                pass
            self.mail.logout()
            print("🔌 Disconnected from Gmail")

    def create_labels(self):
        """Phase 1: Create Gmail labels"""
        print("\n" + "="*60)
        print("PHASE 1: CREATING LABELS")
        print("="*60)

        existing_labels = self.get_existing_labels()

        for label in LABELS_TO_CREATE:
            if label in existing_labels:
                print(f"  ⚠️  Label exists: {label}")
            else:
                try:
                    # Create label using CREATE command
                    result = self.mail.create(f'"{label}"')
                    if result[0] == 'OK':
                        print(f"  ✅ Created: {label}")
                        self.stats['labels_created'].append(label)
                    else:
                        print(f"  ⚠️  Could not create: {label} - {result}")
                except Exception as e:
                    print(f"  ⚠️  Error creating {label}: {str(e)}")

        return True

    def get_existing_labels(self):
        """Get list of existing labels"""
        result, data = self.mail.list()
        labels = []
        if result == 'OK':
            for item in data:
                if item:
                    try:
                        decoded = item.decode('utf-8')
                        # Extract label name from LIST response
                        match = re.search(r'"([^"]+)"$', decoded)
                        if match:
                            labels.append(match.group(1))
                    except:
                        pass
        return labels

    def get_email_date(self, msg):
        """Extract date from email message"""
        date_str = msg.get('Date', '')
        if not date_str:
            return None

        # Use email.utils for robust parsing
        try:
            from email.utils import parsedate_tz, mktime_tz
            parsed = parsedate_tz(date_str)
            if parsed:
                timestamp = mktime_tz(parsed)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception as e:
            pass

        return None

    def get_sender(self, msg):
        """Extract sender email and name"""
        from_header = msg.get('From', '')
        if not from_header:
            return ('unknown', 'unknown')

        # Extract email from "Name <email@domain.com>"
        email_match = re.search(r'<([^>]+)>', from_header)
        if email_match:
            email_addr = email_match.group(1).lower()
            name = from_header.split('<')[0].strip().strip('"')
            return (email_addr, name if name else email_addr)
        else:
            return (from_header.lower(), from_header)

    def categorize_sender(self, sender_email, sender_name, subject=''):
        """Categorize sender based on patterns"""
        full_text = f"{sender_email} {sender_name} {subject}".lower()

        for category, patterns in SENDER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    return category
        return 'personal_business'

    def analyze_and_organize(self):
        """Phase 2 & 3: Analyze emails and organize"""
        print("\n" + "="*60)
        print("PHASE 2 & 3: ANALYZING & ORGANIZING EMAILS")
        print("="*60)

        # Select inbox
        result, data = self.mail.select('inbox')
        if result != 'OK':
            print("❌ Failed to select inbox")
            return

        # Search for all emails
        result, data = self.mail.search(None, 'ALL')
        if result != 'OK':
            print("❌ Failed to search emails")
            return

        email_ids = data[0].split()
        print(f"📊 Found {len(email_ids)} emails in inbox")

        if not email_ids:
            print("📭 Inbox is empty!")
            return

        # Get date thresholds (all timezone-aware)
        now = datetime.now(timezone.utc)
        date_90_days = now - __import__('datetime').timedelta(days=90)
        date_30_days = now - __import__('datetime').timedelta(days=30)
        date_7_days = now - __import__('datetime').timedelta(days=7)

        # Process emails
        batch_size = 50
        total_processed = 0
        processed_ids = []

        for i in range(0, len(email_ids), batch_size):
            batch = email_ids[i:i+batch_size]

            for email_id in batch:
                try:
                    result, data = self.mail.fetch(email_id, '(RFC822)')
                    if result != 'OK':
                        continue

                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Get email details
                    email_date = self.get_email_date(msg)
                    sender_email, sender_name = self.get_sender(msg)
                    subject = msg.get('Subject', '(no subject)')

                    # Track top senders
                    sender_key = f"{sender_name} <{sender_email}>"
                    if sender_key not in self.stats['top_senders']:
                        self.stats['top_senders'][sender_key] = {'count': 0, 'category': None}
                    self.stats['top_senders'][sender_key]['count'] += 1

                    # Skip if no date - try to categorize anyway
                    if not email_date:
                        # Still apply smart labeling
                        category = self.categorize_sender(sender_email, sender_name, subject)
                        if category == 'newsletters':
                            self.apply_smart_label(email_id, category)
                        processed_ids.append(email_id)
                        total_processed += 1
                        continue

                    # Calculate age in days
                    age_days = (now - email_date).days

                    # Phase 2: Age-based archiving
                    if age_days > 90:
                        # Move to 99-Archive and remove from inbox
                        self.move_to_label(email_id, '99-Archive')
                        self.remove_from_inbox(email_id)
                        self.stats['emails_archived_90plus'] += 1

                    elif age_days > 30:
                        # Move to 99-Archive and remove from inbox
                        self.move_to_label(email_id, '99-Archive')
                        self.remove_from_inbox(email_id)
                        self.stats['emails_archived_30_90'] += 1

                    elif age_days > 7:
                        # Add 01-Review label, keep in inbox
                        self.add_label(email_id, '01-Review')
                        self.stats['emails_labeled_7_30'] += 1

                        # Also apply smart labeling
                        category = self.categorize_sender(sender_email, sender_name, subject)
                        self.apply_smart_label(email_id, category)

                    else:
                        # Recent emails: apply smart labels only
                        category = self.categorize_sender(sender_email, sender_name, subject)
                        self.apply_smart_label(email_id, category)

                    processed_ids.append(email_id)
                    total_processed += 1

                    if total_processed % 50 == 0:
                        print(f"  📨 Processed {total_processed} emails...")

                except Exception as e:
                    print(f"  ⚠️  Error processing email {email_id}: {str(e)[:80]}")
                    continue

        print(f"\n✅ Processed {total_processed} emails")

    def apply_smart_label(self, email_id, category):
        """Apply smart label based on category"""
        label_map = {
            'payment_subscription': 'Action-Required',
            'newsletters': 'Read-Later',
            'orders_shipping': '99-Archive',
            'personal_business': 'Review'
        }

        label = label_map.get(category)
        if label:
            self.add_label(email_id, label)

            if category == 'payment_subscription':
                self.stats['smart_labeled_action'] += 1
            elif category == 'newsletters':
                self.stats['smart_labeled_read_later'] += 1
            elif category == 'personal_business':
                self.stats['smart_labeled_review'] += 1

    def add_label(self, email_id, label):
        """Add a label to an email"""
        try:
            # Gmail uses COPY to add labels
            result = self.mail.copy(email_id, label)
            return result[0] == 'OK'
        except Exception as e:
            return False

    def move_to_label(self, email_id, label):
        """Move email to a label (copy)"""
        try:
            result = self.mail.copy(email_id, label)
            return result[0] == 'OK'
        except Exception as e:
            return False

    def remove_from_inbox(self, email_id):
        """Remove email from inbox (mark deleted)"""
        try:
            # Add deleted flag to remove from inbox
            self.mail.store(email_id, '+FLAGS', '\\Deleted')
        except Exception as e:
            pass

    def get_label_counts(self):
        """Get counts of emails per label"""
        print("\n" + "="*60)
        print("LABEL COUNTS")
        print("="*60)

        counts = {}
        result, data = self.mail.list()
        if result == 'OK':
            for item in data:
                try:
                    decoded = item.decode('utf-8')
                    match = re.search(r'"([^"]+)"$', decoded)
                    if match:
                        label_name = match.group(1)
                        # Skip system labels
                        if label_name in ('INBOX', '[Gmail]', '[Google Mail]'):
                            continue
                        # Select the label and count messages
                        try:
                            self.mail.select(f'"{label_name}"')
                            result_count, data_count = self.mail.search(None, 'ALL')
                            if result_count == 'OK':
                                count = len(data_count[0].split())
                                counts[label_name] = count
                                if label_name in LABELS_TO_CREATE or count > 0:
                                    print(f"  📁 {label_name}: {count} emails")
                        except:
                            continue
                except:
                    continue

        # Re-select inbox
        self.mail.select('inbox')
        return counts

    def print_top_senders(self):
        """Print top 20 senders"""
        print("\n" + "="*60)
        print("TOP 20 SENDERS")
        print("="*60)

        sorted_senders = sorted(
            self.stats['top_senders'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:20]

        for i, (sender, info) in enumerate(sorted_senders, 1):
            display = sender[:55] if len(sender) > 55 else sender
            print(f"  {i:2}. {display} ({info['count']} emails)")

    def print_summary(self):
        """Print final summary"""
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)
        print(f"\n📁 Labels Created: {len(self.stats['labels_created'])}")
        for label in self.stats['labels_created']:
            print(f"   ✅ {label}")

        print(f"\n📨 Age-Based Processing:")
        print(f"   📦 >90 days archived: {self.stats['emails_archived_90plus']}")
        print(f"   📦 30-90 days archived: {self.stats['emails_archived_30_90']}")
        print(f"   📋 7-30 days → 01-Review: {self.stats['emails_labeled_7_30']}")

        print(f"\n🧠 Smart Labeling:")
        print(f"   🔴 Action-Required: {self.stats['smart_labeled_action']}")
        print(f"   🟢 Read-Later: {self.stats['smart_labeled_read_later']}")
        print(f"   🟡 Review: {self.stats['smart_labeled_review']}")

def main():
    organizer = GmailOrganizer()

    try:
        # Phase 1: Connect and create labels
        organizer.connect()
        organizer.create_labels()

        # Phase 2 & 3: Analyze and organize emails
        organizer.analyze_and_organize()

        # Expunge deleted messages
        organizer.mail.expunge()

        # Get final label counts
        organizer.get_label_counts()

        # Print top senders
        organizer.print_top_senders()

        # Print final summary
        organizer.print_summary()

        print("\n" + "="*60)
        print("✅ GMAIL ORGANIZATION COMPLETE!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        organizer.disconnect()

if __name__ == "__main__":
    main()
