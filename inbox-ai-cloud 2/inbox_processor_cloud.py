#!/usr/bin/env python3
"""
Inbox AI Cloud v3.1 - Universal Email Automation
Cloud-native with GitHub Actions support
Multi-provider: Gmail, Outlook, IONOS, iCloud, Yahoo, Zoho, GMX, Custom

Features:
- Multi-account support (unlimited)
- IMAP/SMTP connection pooling
- Circuit breaker pattern
- SQLite state management (GitHub Actions compatible)
- Universal provider auto-detection
"""
import os
import sys
import json
import time
import signal
import logging
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from functools import wraps
import ssl
import smtplib
from pathlib import Path
import sqlite3
import hashlib
import threading
from collections import deque
import re

# Cloud-native logging (stdout for GitHub Actions)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('inbox_ai_cloud')

# State directory (GitHub Actions compatible)
STATE_DIR = Path(os.environ.get('STATE_DIR', os.path.expanduser('~/.inbox-ai-state')))
STATE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = STATE_DIR / 'inbox_ai.db'

# ==================== PROVIDER CONFIGURATIONS ====================

PROVIDER_CONFIGS = {
    'gmail': {
        'imap_server': 'imap.gmail.com',
        'imap_port': 993,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'requires_app_password': True,
        'setup_url': 'https://myaccount.google.com/apppasswords'
    },
    'outlook': {
        'imap_server': 'outlook.office365.com',
        'imap_port': 993,
        'smtp_server': 'smtp.office365.com',
        'smtp_port': 587,
        'requires_app_password': False,
        'setup_url': 'https://outlook.live.com/mail/0/options/mail/accounts/popImap'
    },
    'ionos': {
        'imap_server': 'imap.ionos.de',
        'imap_port': 993,
        'smtp_server': 'smtp.ionos.de',
        'smtp_port': 587,
        'requires_app_password': False,
        'setup_url': 'https://id.ionos.de/'
    },
    'icloud': {
        'imap_server': 'imap.mail.me.com',
        'imap_port': 993,
        'smtp_server': 'smtp.mail.me.com',
        'smtp_port': 587,
        'requires_app_password': True,
        'setup_url': 'https://appleid.apple.com/account/manage'
    },
    'yahoo': {
        'imap_server': 'imap.mail.yahoo.com',
        'imap_port': 993,
        'smtp_server': 'smtp.mail.yahoo.com',
        'smtp_port': 587,
        'requires_app_password': True,
        'setup_url': 'https://login.yahoo.com/account/security'
    },
    'zoho': {
        'imap_server': 'imap.zoho.com',
        'imap_port': 993,
        'smtp_server': 'smtp.zoho.com',
        'smtp_port': 587,
        'requires_app_password': False,
        'setup_url': 'https://mail.zoho.com/zm/#settings/accounts/imap'
    },
    'gmx': {
        'imap_server': 'imap.gmx.net',
        'imap_port': 993,
        'smtp_server': 'mail.gmx.net',
        'smtp_port': 587,
        'requires_app_password': False,
        'setup_url': 'https://www.gmx.net/mail/'
    },
    'fastmail': {
        'imap_server': 'imap.fastmail.com',
        'imap_port': 993,
        'smtp_server': 'smtp.fastmail.com',
        'smtp_port': 587,
        'requires_app_password': True,
        'setup_url': 'https://www.fastmail.com/settings/security/apps'
    }
}

def detect_provider(email_address: str) -> str:
    """Auto-detect email provider from address"""
    domain = email_address.split('@')[1].lower()
    
    provider_map = {
        'gmail.com': 'gmail',
        'googlemail.com': 'gmail',
        'outlook.com': 'outlook',
        'hotmail.com': 'outlook',
        'live.com': 'outlook',
        'msn.com': 'outlook',
        'office365.com': 'outlook',
        'ionos.de': 'ionos',
        '1und1.de': 'ionos',
        'me.com': 'icloud',
        'icloud.com': 'icloud',
        'mac.com': 'icloud',
        'yahoo.com': 'yahoo',
        'ymail.com': 'yahoo',
        'zoho.com': 'zoho',
        'gmx.de': 'gmx',
        'gmx.net': 'gmx',
        'gmx.at': 'gmx',
        'fastmail.com': 'fastmail',
        'fastmail.fm': 'fastmail'
    }
    
    return provider_map.get(domain, 'custom')

# ==================== DATA MODELS ====================

@dataclass
class EmailAccount:
    """Single email account configuration"""
    name: str
    email: str
    password: str
    provider: str = 'auto'
    from_name: str = "Your Team"
    enabled: bool = True
    auto_reply: bool = True
    escalation_threshold: float = 0.7
    max_replies_per_hour: int = 20
    calendly_link: str = ""
    escalation_phone: str = ""
    imap_server: str = ""
    imap_port: int = 993
    smtp_server: str = ""
    smtp_port: int = 587
    
    def __post_init__(self):
        if self.provider == 'auto':
            self.provider = detect_provider(self.email)
        
        # Auto-fill provider defaults if not specified
        if self.provider in PROVIDER_CONFIGS:
            config = PROVIDER_CONFIGS[self.provider]
            if not self.imap_server:
                self.imap_server = config['imap_server']
            if not self.imap_port:
                self.imap_port = config['imap_port']
            if not self.smtp_server:
                self.smtp_server = config['smtp_server']
            if not self.smtp_port:
                self.smtp_port = config['smtp_port']

# ==================== CIRCUIT BREAKER ====================

class CircuitBreaker:
    """Prevents cascade failures"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        with self._lock:
            if self.state == 'OPEN':
                if time.time() - self.last_failure > self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise Exception(f"Circuit breaker OPEN - skipping call")
        
        try:
            result = func(*args, **kwargs)
            with self._lock:
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failures = 0
                    logger.info("Circuit breaker CLOSED - service recovered")
            return result
        except Exception as e:
            with self._lock:
                self.failures += 1
                self.last_failure = time.time()
                if self.failures >= self.failure_threshold:
                    self.state = 'OPEN'
                    logger.error(f"Circuit breaker OPEN after {self.failures} failures")
            raise e

# ==================== DATABASE ====================

class StateManager:
    """SQLite-based state management for GitHub Actions"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_emails (
                    id TEXT PRIMARY KEY,
                    account_name TEXT,
                    from_addr TEXT,
                    subject TEXT,
                    category TEXT,
                    priority REAL,
                    escalation INTEGER,
                    action TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reply_stats (
                    account_name TEXT,
                    hour INTEGER,
                    reply_count INTEGER DEFAULT 0,
                    PRIMARY KEY (account_name, hour)
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_processed_time 
                ON processed_emails(processed_at)
            ''')
            conn.commit()
    
    def is_processed(self, email_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT 1 FROM processed_emails WHERE id = ?',
                (email_id,)
            )
            return cursor.fetchone() is not None
    
    def mark_processed(self, email_id: str, account: str, from_addr: str,
                       subject: str, category: str, priority: float,
                       escalation: bool, action: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR IGNORE INTO processed_emails 
                (id, account_name, from_addr, subject, category, priority, escalation, action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (email_id, account, from_addr, subject, category, priority,
                  int(escalation), action))
            conn.commit()
    
    def get_reply_count_this_hour(self, account_name: str) -> int:
        current_hour = datetime.now().hour
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT reply_count FROM reply_stats 
                WHERE account_name = ? AND hour = ?
            ''', (account_name, current_hour))
            row = cursor.fetchone()
            return row[0] if row else 0
    
    def increment_reply_count(self, account_name: str):
        current_hour = datetime.now().hour
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO reply_stats (account_name, hour, reply_count)
                VALUES (?, ?, 1)
                ON CONFLICT(account_name, hour) DO UPDATE SET
                reply_count = reply_count + 1
            ''', (account_name, current_hour))
            conn.commit()
    
    def get_stats(self, hours: int = 24) -> Dict:
        """Get processing statistics"""
        with sqlite3.connect(self.db_path) as conn:
            since = datetime.now() - timedelta(hours=hours)
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN escalation = 1 THEN 1 ELSE 0 END) as escalations,
                    category
                FROM processed_emails
                WHERE processed_at > ?
                GROUP BY category
            ''', (since,))
            rows = cursor.fetchall()
            
            stats = {'total': 0, 'escalations': 0, 'by_category': {}}
            for row in rows:
                total, esc, cat = row
                stats['total'] += total
                stats['escalations'] += esc
                stats['by_category'][cat] = total
            
            return stats

# ==================== EMAIL PROCESSING ====================

class EmailProcessor:
    """Process emails for a single account"""
    
    CATEGORIES = {
        'booking': ['meeting', 'termin', 'calendly', 'appointment', 'schedule', 'call', 'buchung'],
        'support': ['support', 'problem', 'error', 'issue', 'bug', 'help', 'broken', 'hilfe', 'fehler'],
        'inquiry': ['quote', 'pricing', 'inquiry', 'partnership', 'angebot', 'anfrage', 'preis'],
        'billing': ['invoice', 'payment', 'billing', 'rechnung', 'zahlung', 'rechnungs'],
        'legal': ['legal', 'gdpr', 'dsgvo', 'complaint', 'beschwerde', 'lawyer', 'anwalt'],
        'spam': ['unsubscribe', 'newsletter', 'no-reply', 'noreply', 'promo', 'marketing', 'werbung']
    }
    
    def __init__(self, account: EmailAccount, state: StateManager, mode: str = 'auto'):
        self.account = account
        self.state = state
        self.mode = mode
        self.circuit = CircuitBreaker()
    
    def generate_email_id(self, from_addr: str, subject: str, date_str: str) -> str:
        """Generate unique ID for deduplication"""
        content = f"{from_addr}|{subject}|{date_str}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def categorize(self, subject: str, body: str, from_addr: str) -> Tuple[str, float, bool]:
        """Categorize email and calculate urgency"""
        subject_lower = subject.lower()
        body_lower = body[:2000].lower()  # First 2000 chars
        
        # Check spam first
        spam_keywords = self.CATEGORIES['spam']
        if any(k in from_addr.lower() or k in subject_lower for k in spam_keywords):
            return 'spam', 0.0, False
        
        # Calculate urgency
        urgent_words = ['urgent', 'asap', 'dringend', 'sofort', 'critical', 'emergency', 
                       'down', 'broken', 'failed', 'immediately', 'wichtig', 'eilig']
        urgency_score = sum(1 for w in urgent_words if w in subject_lower or w in body_lower)
        urgency = min(0.3 + (urgency_score / len(urgent_words)) * 0.7, 1.0)
        
        # Determine category
        for cat, keywords in self.CATEGORIES.items():
            if cat == 'spam':
                continue
            if any(k in subject_lower for k in keywords):
                category = cat
                break
        else:
            category = 'general'
        
        # Escalation rules
        requires_escalation = (
            urgency > 0.6 or
            category == 'legal' or
            'complaint' in body_lower or
            len(body) > 5000 or
            any(w in subject_lower for w in ['lawsuit', 'klage', 'anwalt', 'lawyer'])
        )
        
        return category, urgency, requires_escalation
    
    def generate_summary(self, body: str) -> str:
        """Extract summary from email body"""
        lines = [l.strip() for l in body.split('\n') if l.strip()]
        for line in lines:
            if len(line) > 40 and not line.startswith('>'):
                return line[:200] + ('...' if len(line) > 200 else '')
        return lines[0][:200] if lines else "No summary available"
    
    def should_reply(self, category: str, urgency: float, escalated: bool) -> bool:
        """Determine if we should auto-reply"""
        if self.mode == 'monitor':
            return False
        if self.mode == 'hybrid':
            return False  # Draft only, don't send
        if not self.account.auto_reply:
            return False
        if escalated:
            return False
        if category == 'spam':
            return False
        
        # Rate limiting
        reply_count = self.state.get_reply_count_this_hour(self.account.name)
        if reply_count >= self.account.max_replies_per_hour:
            logger.warning(f"Rate limit reached for {self.account.name}")
            return False
        
        return True
    
    def generate_reply(self, category: str, subject: str, has_calendly: bool = False) -> str:
        """Generate contextual auto-reply"""
        
        greeting = "Hallo," if self.account.provider in ['ionos', 'gmx'] else "Hi there,"
        
        replies = {
            'booking': f"""{greeting}

Thank you for your meeting request. 

You can book a time directly here: {self.account.calendly_link or '[CALENDLY_LINK]'}

Looking forward to speaking with you!

Best regards""",
            
            'support': f"""{greeting}

Thank you for reaching out about this issue. 

I've received your message and will investigate this promptly. For urgent matters, please call: {self.account.escalation_phone or '[PHONE]'}

I'll update you within 2 hours.

Best regards""",
            
            'inquiry': f"""{greeting}

Thank you for your inquiry!

I've received your request and will prepare a detailed response within 24 hours.

If you'd like to discuss this sooner, feel free to book a call: {self.account.calendly_link or '[CALENDLY_LINK]'}

Best regards""",
            
            'billing': f"""{greeting}

Thank you for your message regarding billing.

This has been forwarded to our accounting team. You'll receive a response within 1 business day.

Best regards""",
            
            'general': f"""{greeting}

Thank you for your email.

I've received your message and will respond within 24 hours.

Best regards"""
        }
        
        return replies.get(category, replies['general'])

# ==================== IMAP/SMTP OPERATIONS ====================

class EmailClient:
    """Handle IMAP/SMTP operations with connection pooling"""
    
    def __init__(self, account: EmailAccount):
        self.account = account
        self.imap_conn = None
        self.smtp_conn = None
        self.circuit = CircuitBreaker()
    
    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server"""
        def _connect():
            conn = imaplib.IMAP4_SSL(
                self.account.imap_server,
                self.account.imap_port
            )
            conn.login(self.account.email, self.account.password)
            return conn
        
        return self.circuit.call(_connect)
    
    def connect_smtp(self) -> smtplib.SMTP:
        """Connect to SMTP server"""
        def _connect():
            conn = smtplib.SMTP(self.account.smtp_server, self.account.smtp_port)
            conn.starttls()
            conn.login(self.account.email, self.account.password)
            return conn
        
        return self.circuit.call(_connect)
    
    def fetch_unread(self, limit: int = 50) -> List[Dict]:
        """Fetch unread emails"""
        try:
            conn = self.connect_imap()
            conn.select('INBOX')
            
            _, messages = conn.search(None, 'UNSEEN')
            email_ids = messages[0].split()[-limit:]  # Last N emails
            
            emails = []
            for eid in email_ids:
                try:
                    _, msg_data = conn.fetch(eid, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Extract body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    emails.append({
                        'id': eid.decode(),
                        'from': msg['From'],
                        'subject': msg['Subject'] or '(No Subject)',
                        'date': msg['Date'] or '',
                        'body': body[:10000]  # Limit size
                    })
                except Exception as e:
                    logger.error(f"Error parsing email {eid}: {e}")
                    continue
            
            conn.close()
            conn.logout()
            return emails
            
        except Exception as e:
            logger.error(f"IMAP error for {self.account.name}: {e}")
            return []
    
    def send_reply(self, to_addr: str, subject: str, body: str) -> bool:
        """Send email reply"""
        try:
            conn = self.connect_smtp()
            
            msg = MIMEMultipart()
            msg['From'] = f"{self.account.from_name} <{self.account.email}>"
            msg['To'] = to_addr
            msg['Subject'] = f"Re: {subject}"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            conn.send_message(msg)
            conn.quit()
            return True
            
        except Exception as e:
            logger.error(f"SMTP error for {self.account.name}: {e}")
            return False

# ==================== MAIN PROCESSOR ====================

class InboxAICloud:
    """Main processor coordinating all accounts"""
    
    def __init__(self, config_path: Optional[str] = None, mode: str = 'auto'):
        self.mode = mode
        self.state = StateManager()
        self.accounts: List[EmailAccount] = []
        
        # Load from environment (GitHub Actions) or config file
        self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[str]):
        """Load accounts from environment or config"""
        # Try environment variables first (GitHub Actions)
        env_config = os.environ.get('INBOX_AI_CONFIG')
        if env_config:
            try:
                config = json.loads(env_config)
                for acc in config.get('accounts', []):
                    self.accounts.append(EmailAccount(**acc))
                logger.info(f"Loaded {len(self.accounts)} accounts from environment")
                return
            except Exception as e:
                logger.error(f"Failed to parse env config: {e}")
        
        # Fall back to config file
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                config = json.load(f)
                for acc in config.get('accounts', []):
                    self.accounts.append(EmailAccount(**acc))
                logger.info(f"Loaded {len(self.accounts)} accounts from file")
        else:
            logger.error("No configuration found!")
    
    def process_account(self, account: EmailAccount) -> Dict:
        """Process all emails for one account"""
        if not account.enabled:
            return {'account': account.name, 'skipped': True}
        
        logger.info(f"Processing account: {account.name} ({account.email})")
        
        client = EmailClient(account)
        processor = EmailProcessor(account, self.state, self.mode)
        
        # Fetch emails
        emails = client.fetch_unread(limit=20)
        logger.info(f"Found {len(emails)} unread emails")
        
        results = {
            'account': account.name,
            'processed': 0,
            'replied': 0,
            'escalated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for email_data in emails:
            try:
                # Generate ID
                email_id = processor.generate_email_id(
                    email_data['from'],
                    email_data['subject'],
                    email_data['date']
                )
                
                # Check if already processed
                if self.state.is_processed(email_id):
                    results['skipped'] += 1
                    continue
                
                # Process
                category, priority, escalated = processor.categorize(
                    email_data['subject'],
                    email_data['body'],
                    email_data['from']
                )
                
                summary = processor.generate_summary(email_data['body'])
                
                # Determine action
                if escalated:
                    action = 'escalated'
                    results['escalated'] += 1
                elif category == 'spam':
                    action = 'archived'
                else:
                    should_send = processor.should_reply(category, priority, escalated)
                    if should_send:
                        reply_body = processor.generate_reply(category, email_data['subject'])
                        success = client.send_reply(email_data['from'], email_data['subject'], reply_body)
                        if success:
                            action = 'replied'
                            results['replied'] += 1
                            self.state.increment_reply_count(account.name)
                        else:
                            action = 'reply_failed'
                    else:
                        action = 'processed'
                
                # Mark as processed
                self.state.mark_processed(
                    email_id, account.name, email_data['from'],
                    email_data['subject'], category, priority,
                    escalated, action
                )
                
                results['processed'] += 1
                
                # Log
                logger.info(f"  [{category}] {email_data['subject'][:50]}... -> {action}")
                
            except Exception as e:
                logger.error(f"Error processing email: {e}")
                results['errors'] += 1
        
        return results
    
    def run(self) -> Dict:
        """Run processing for all accounts"""
        logger.info("=" * 60)
        logger.info("Inbox AI Cloud v3.1 - Starting processing")
        logger.info(f"Mode: {self.mode}")
        logger.info(f"Accounts: {len(self.accounts)}")
        logger.info("=" * 60)
        
        all_results = []
        for account in self.accounts:
            try:
                result = self.process_account(account)
                all_results.append(result)
            except Exception as e:
                logger.error(f"Failed to process account {account.name}: {e}")
                all_results.append({
                    'account': account.name,
                    'error': str(e)
                })
        
        # Summary
        stats = self.state.get_stats(hours=24)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'mode': self.mode,
            'accounts': all_results,
            'stats_24h': stats
        }
        
        logger.info("=" * 60)
        logger.info("Processing complete")
        logger.info(f"Total processed (24h): {stats['total']}")
        logger.info(f"Escalations (24h): {stats['escalations']}")
        logger.info("=" * 60)
        
        return summary

# ==================== CLI ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Inbox AI Cloud - Universal Email Automation')
    parser.add_argument('--mode', choices=['monitor', 'hybrid', 'auto'], default='auto',
                       help='Processing mode: monitor=read-only, hybrid=draft-only, auto=full automation')
    parser.add_argument('--config', help='Path to config JSON file')
    parser.add_argument('--test', action='store_true', help='Test connections only')
    
    args = parser.parse_args()
    
    if args.test:
        # Test mode - just verify connections
        processor = InboxAICloud(args.config, mode='monitor')
        print(f"Testing {len(processor.accounts)} account(s)...")
        for acc in processor.accounts:
            try:
                client = EmailClient(acc)
                conn = client.connect_imap()
                conn.select('INBOX')
                _, data = conn.search(None, 'ALL')
                count = len(data[0].split())
                conn.close()
                conn.logout()
                print(f"✅ {acc.name}: Connected ({count} emails in inbox)")
            except Exception as e:
                print(f"❌ {acc.name}: Failed - {e}")
        return
    
    # Run processing
    processor = InboxAICloud(args.config, mode=args.mode)
    result = processor.run()
    
    # Output JSON for GitHub Actions
    print(json.dumps(result, indent=2, default=str))

if __name__ == '__main__':
    main()
