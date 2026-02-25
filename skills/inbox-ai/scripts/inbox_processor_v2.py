#!/usr/bin/env python3
"""
Inbox AI - Main Email Processor
Monitors inbox, categorizes, prioritizes, and auto-replies

Improvements:
- Structured logging
- Retry logic with exponential backoff
- Rate limiting for outgoing emails
- Config validation
- Graceful shutdown handling
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
from dataclasses import dataclass, field
from functools import wraps
import ssl
import smtplib
from pathlib import Path
import sqlite3
import hashlib

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser('~/.openclaw/logs/inbox-ai.log'))
    ]
)
logger = logging.getLogger('inbox_ai')

# Ensure log directory exists
os.makedirs(os.path.expanduser('~/.openclaw/logs'), exist_ok=True)

# Load config from environment
CONFIG_FILE = os.path.expanduser("~/.openclaw/workspace/inbox-ai-config.env")


@dataclass
class EmailConfig:
    """Validated email configuration"""
    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    email_username: str
    email_password: str
    from_name: str = "Your Team"
    auto_reply_enabled: bool = True
    escalation_threshold: float = 0.7
    summary_language: str = "de"
    max_auto_reply_per_hour: int = 20
    calendly_link: str = ""
    
    @classmethod
    def from_dict(cls, config: Dict[str, str]) -> 'EmailConfig':
        """Create config from dictionary with validation"""
        required = ['IMAP_SERVER', 'SMTP_SERVER', 'EMAIL_USERNAME', 'EMAIL_PASSWORD']
        missing = [f for f in required if not config.get(f)]
        if missing:
            raise ValueError(f"Missing required config fields: {missing}")
        
        return cls(
            imap_server=config['IMAP_SERVER'],
            imap_port=int(config.get('IMAP_PORT', 993)),
            smtp_server=config['SMTP_SERVER'],
            smtp_port=int(config.get('SMTP_PORT', 587)),
            email_username=config['EMAIL_USERNAME'],
            email_password=config['EMAIL_PASSWORD'],
            from_name=config.get('FROM_NAME', 'Your Team'),
            auto_reply_enabled=config.get('AUTO_REPLY_ENABLED', 'true').lower() == 'true',
            escalation_threshold=float(config.get('ESCALATION_THRESHOLD', 0.7)),
            summary_language=config.get('SUMMARY_LANGUAGE', 'de'),
            max_auto_reply_per_hour=int(config.get('MAX_AUTO_REPLY_PER_HOUR', 20)),
            calendly_link=config.get('CALENDLY_LINK', '')
        )


@dataclass
class ProcessingResult:
    """Result of email processing"""
    id: str
    from_addr: str
    subject: str
    category: str
    priority: float
    escalation: bool
    summary: str
    action: str
    processed_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


class PersistentJobQueue:
    """
    Persistent SQLite-based job queue for email processing.
    Ensures no emails are lost on crash/restart.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.expanduser('~/.openclaw/inbox-ai/job-queue.db')
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Jobs table - stores emails to be processed
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT UNIQUE NOT NULL,
                    message_id TEXT,
                    sender TEXT,
                    subject TEXT,
                    body_preview TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT,
                    error TEXT,
                    retry_count INTEGER DEFAULT 0
                )
            ''')
            
            # Processed emails tracking (idempotency)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_emails (
                    message_id TEXT PRIMARY KEY,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action TEXT,
                    category TEXT
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_email_id ON jobs(email_id)')
            
            conn.commit()
    
    def add_job(self, email_id: str, message_id: str, sender: str, 
                subject: str, body: str) -> bool:
        """Add a new email job to the queue. Returns False if already exists."""
        # Check if already processed (idempotency)
        if self.is_processed(message_id):
            logger.debug(f"Email {message_id} already processed, skipping")
            return False
        
        body_preview = body[:500] if body else ''
        
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO jobs 
                    (email_id, message_id, sender, subject, body_preview, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                ''', (email_id, message_id, sender, subject, body_preview))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to add job: {e}")
            return False
    
    def get_pending_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending jobs for processing"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE status = 'pending' 
                AND retry_count < 3
                ORDER BY created_at ASC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_processing(self, job_id: int) -> None:
        """Mark job as being processed"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE jobs 
                SET status = 'processing', started_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (job_id,))
            conn.commit()
    
    def mark_completed(self, job_id: int, result: str, action: str,
                       message_id: str, category: str) -> None:
        """Mark job as completed"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE jobs 
                SET status = 'completed', 
                    completed_at = CURRENT_TIMESTAMP,
                    result = ?
                WHERE id = ?
            ''', (result, job_id))
            
            # Track as processed for idempotency
            cursor.execute('''
                INSERT OR REPLACE INTO processed_emails 
                (message_id, action, category)
                VALUES (?, ?, ?)
            ''', (message_id, action, category))
            conn.commit()
    
    def mark_failed(self, job_id: int, error: str) -> None:
        """Mark job as failed with retry"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE jobs 
                SET status = 'pending',
                    error = ?,
                    retry_count = retry_count + 1
                WHERE id = ?
            ''', (error, job_id))
            conn.commit()
    
    def is_processed(self, message_id: str) -> bool:
        """Check if email was already processed (idempotency)"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM processed_emails WHERE message_id = ?',
                (message_id,)
            )
            return cursor.fetchone() is not None
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status, COUNT(*) FROM jobs GROUP BY status
            ''')
            stats = dict(cursor.fetchall())
            cursor.execute('SELECT COUNT(*) FROM processed_emails')
            stats['total_processed_ever'] = cursor.fetchone()[0]
            return stats


class RateLimiter:
    """Rate limiter for outgoing emails"""
    
    def __init__(self, max_per_hour: int = 20):
        self.max_per_hour = max_per_hour
        self.sent_times: List[datetime] = []
        self._lock = False
    
    def can_send(self) -> bool:
        """Check if we can send another email"""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        self.sent_times = [t for t in self.sent_times if t > cutoff]
        return len(self.sent_times) < self.max_per_hour
    
    def record_sent(self):
        """Record that we sent an email"""
        self.sent_times.append(datetime.now())
    
    def wait_time(self) -> float:
        """Get seconds to wait before next send is allowed"""
        if not self.sent_times:
            return 0
        oldest = min(self.sent_times)
        wait = 3600 - (datetime.now() - oldest).total_seconds()
        return max(0, wait)


def retry_on_error(max_retries: int = 3, delay: float = 1.0, exceptions: Tuple = (Exception,)):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator


class InboxProcessor:
    """Main email processor with persistent queue and improved error handling"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.max_auto_reply_per_hour)
        self.job_queue = PersistentJobQueue()
        self._shutdown = False
        self._results: List[ProcessingResult] = []
        self._smtp_pool: List[smtplib.SMTP] = []
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown = True
        self._close_smtp_pool()
    
    def load_config() -> EmailConfig:
        """Load and validate configuration from env file"""
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#') and line:
                        key, value = line.split('=', 1)
                        config[key] = value
        
        if not config:
            raise ValueError(f"Config not found or empty at {CONFIG_FILE}")
        
        return EmailConfig.from_dict(config)
    
    @retry_on_error(max_retries=3, delay=1.0, exceptions=(imaplib.IMAP4.error, ConnectionError))
    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to IMAP server with retry logic"""
        logger.info(f"Connecting to IMAP server {self.config.imap_server}...")
        imap = imaplib.IMAP4_SSL(self.config.imap_server, self.config.imap_port)
        imap.login(self.config.email_username, self.config.email_password)
        logger.info("IMAP connection established")
        return imap
    
    def categorize_email(self, subject: str, body: str, sender: str) -> Tuple[str, float, bool]:
        """
        Categorize email by type
        Returns: category, priority_score (0-1), requires_escalation
        """
        subject_lower = subject.lower()
        body_lower = body.lower()
        
        # Spam detection
        spam_keywords = ['unsubscribe', 'werbung', 'newsletter', 'no-reply', 'marketing', 'promo']
        if any(k in sender.lower() or k in subject_lower for k in spam_keywords):
            return 'spam', 0.0, False
        
        # Urgency indicators
        urgent_keywords = ['dringend', 'urgent', 'asap', 'sofort', 'wichtig', 'deadline', 'critical']
        urgency_score = sum(1 for k in urgent_keywords if k in subject_lower or k in body_lower) / len(urgent_keywords)
        
        # Category detection
        if any(k in subject_lower for k in ['termin', 'meeting', 'calendly', 'buchung', 'appointment']):
            category = 'booking'
        elif any(k in subject_lower for k in ['support', 'hilfe', 'problem', 'fehler', 'bug', 'issue']):
            category = 'support'
        elif any(k in subject_lower for k in ['angebot', 'preis', 'kosten', 'angebot', 'quote', 'price', 'cost']):
            category = 'inquiry'
        elif any(k in subject_lower for k in ['rechnung', 'invoice', 'zahlung', 'payment', 'bill']):
            category = 'billing'
        else:
            category = 'general'
        
        # Priority scoring (0-1)
        priority = min(0.3 + urgency_score * 0.7, 1.0)
        
        # Escalation rules
        requires_escalation = (
            urgency_score > 0.6 or  # High urgency
            any(k in body_lower for k in ['beschwerde', 'complaint', 'klage', 'lawsuit', 'legal']) or
            len(body) > 3000  # Very complex
        )
        
        return category, priority, requires_escalation
    
    def generate_summary(self, subject: str, body: str) -> str:
        """Generate TL;DR summary"""
        lines = body.strip().split('\n')
        # Get first substantial line
        for line in lines:
            line = line.strip()
            if len(line) > 20 and not line.startswith('>'):
                return line[:200] + ('...' if len(line) > 200 else '')
        return subject
    
    def should_auto_reply(self, category: str, priority: float, requires_escalation: bool) -> Tuple[bool, str]:
        """Determine if we should auto-reply with reason"""
        if not self.config.auto_reply_enabled:
            return False, "auto_reply_disabled"
        if requires_escalation:
            return False, "requires_escalation"
        if category == 'spam':
            return False, "spam_detected"
        if priority > self.config.escalation_threshold:
            return False, "high_priority"
        if not self.rate_limiter.can_send():
            return False, "rate_limited"
        return True, "ok"
    
    def generate_reply(self, category: str, subject: str, body: str) -> str:
        """Generate contextual auto-reply (plain text)"""
        templates = {
            'booking': f"""Hallo,

vielen Dank für Ihre Terminanfrage. Ich habe Ihre Nachricht erhalten und werde mich in Kürze mit verfügbaren Terminen bei Ihnen melden.

Alternativ können Sie direkt einen Termin buchen:
{self.config.calendly_link or '[Calendly-Link einfügen]'}

Mit freundlichen Grüßen
{self.config.from_name}""",
            
            'inquiry': f"""Hallo,

vielen Dank für Ihr Interesse. Ich habe Ihre Anfrage erhalten und prüfe aktuell die Details. Sie erhalten innerhalb der nächsten 24 Stunden ein maßgeschneidertes Angebot.

Bei dringenden Fragen erreichen Sie mich auch telefonisch.

Mit freundlichen Grüßen
{self.config.from_name}""",
            
            'support': f"""Hallo,

vielen Dank für Ihre Nachricht. Ich habe Ihr Anliegen verstanden und arbeite daran.

Ich werde mich schnellstmöglich mit einer Lösung oder Rückfragen bei Ihnen melden.

Mit freundlichen Grüßen
{self.config.from_name}""",
            
            'general': f"""Hallo,

vielen Dank für Ihre E-Mail. Ich habe Ihre Nachricht erhalten und werde mich so schnell wie möglich bei Ihnen melden.

Mit freundlichen Grüßen
{self.config.from_name}"""
        }
        
        return templates.get(category, templates['general'])
    
    def generate_html_reply(self, category: str, subject: str, body: str) -> str:
        """Generate professional HTML auto-reply with branding"""
        
        # Brand colors and styling
        primary_color = "#2563eb"  # Blue
        text_color = "#374151"     # Gray-700
        bg_color = "#f9fafb"       # Gray-50
        
        html_templates = {
            'booking': f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: {bg_color};">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="color: {primary_color}; margin: 0 0 20px 0; font-size: 24px;">Terminanfrage erhalten</h2>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    Hallo,
                </p>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    vielen Dank für Ihre Terminanfrage. Ich habe Ihre Nachricht erhalten und werde mich in Kürze mit verfügbaren Terminen bei Ihnen melden.
                </p>
                
                <div style="background-color: {bg_color}; border-left: 4px solid {primary_color}; padding: 20px; margin: 25px 0;">
                    <p style="color: {text_color}; font-size: 15px; margin: 0 0 15px 0;">
                        <strong>Schneller buchen:</strong>
                    </p>
                    <a href="{self.config.calendly_link or '#'}" 
                       style="display: inline-block; background-color: {primary_color}; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: 500;">
                        Termin direkt buchen →
                    </a>
                </div>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 30px 0 0 0;">
                    Mit freundlichen Grüßen<br>
                    <strong style="color: {primary_color};">{self.config.from_name}</strong>
                </p>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px 30px; background-color: {bg_color}; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 12px; margin: 0;">
                    Diese E-Mail wurde automatisch generiert. Bei dringenden Anliegen antworten Sie einfach auf diese Nachricht.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>""",
            
            'inquiry': f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: {bg_color};">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="color: {primary_color}; margin: 0 0 20px 0; font-size: 24px;">Anfrage erhalten</h2>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    Hallo,
                </p>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    vielen Dank für Ihr Interesse. Ich habe Ihre Anfrage erhalten und prüfe aktuell die Details.
                </p>
                
                <div style="background-color: #dbeafe; border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
                    <p style="color: {primary_color}; font-size: 15px; margin: 0; font-weight: 500;">
                        📋 Sie erhalten innerhalb der nächsten <strong>24 Stunden</strong> ein maßgeschneidertes Angebot.
                    </p>
                </div>
                
                <p style="color: {text_color}; font-size: 15px; line-height: 1.6; margin: 20px 0;">
                    Bei dringenden Fragen erreichen Sie mich auch telefonisch.
                </p>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 30px 0 0 0;">
                    Mit freundlichen Grüßen<br>
                    <strong style="color: {primary_color};">{self.config.from_name}</strong>
                </p>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px 30px; background-color: {bg_color}; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 12px; margin: 0;">
                    Diese E-Mail wurde automatisch generiert. Bei dringenden Anliegen antworten Sie einfach auf diese Nachricht.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>""",
            
            'support': f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: {bg_color};">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="color: {primary_color}; margin: 0 0 20px 0; font-size: 24px;">Support-Anfrage erhalten</h2>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    Hallo,
                </p>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    vielen Dank für Ihre Nachricht. Ich habe Ihr Anliegen verstanden und arbeite bereits daran.
                </p>
                
                <div style="background-color: #fef3c7; border-radius: 8px; padding: 20px; margin: 25px 0; border-left: 4px solid #f59e0b;">
                    <p style="color: #92400e; font-size: 15px; margin: 0;">
                        ⚡ Ich werde mich schnellstmöglich mit einer Lösung oder Rückfragen bei Ihnen melden.
                    </p>
                </div>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 30px 0 0 0;">
                    Mit freundlichen Grüßen<br>
                    <strong style="color: {primary_color};">{self.config.from_name}</strong>
                </p>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px 30px; background-color: {bg_color}; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 12px; margin: 0;">
                    Diese E-Mail wurde automatisch generiert. Bei dringenden Anliegen antworten Sie einfach auf diese Nachricht.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>""",
            
            'general': f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: {bg_color};">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="color: {primary_color}; margin: 0 0 20px 0; font-size: 24px;">Nachricht erhalten</h2>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    Hallo,
                </p>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    vielen Dank für Ihre E-Mail. Ich habe Ihre Nachricht erhalten und werde mich so schnell wie möglich bei Ihnen melden.
                </p>
                
                <p style="color: {text_color}; font-size: 16px; line-height: 1.6; margin: 30px 0 0 0;">
                    Mit freundlichen Grüßen<br>
                    <strong style="color: {primary_color};">{self.config.from_name}</strong>
                </p>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px 30px; background-color: {bg_color}; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 12px; margin: 0;">
                    Diese E-Mail wurde automatisch generiert. Bei dringenden Anliegen antworten Sie einfach auf diese Nachricht.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>"""
        }
        
        return html_templates.get(category, html_templates['general'])
    
    @retry_on_error(max_retries=2, delay=2.0, exceptions=(smtplib.SMTPException, ConnectionError))
    def send_reply(self, to_email: str, subject: str, body: str, in_reply_to: str, 
                   html_body: Optional[str] = None) -> bool:
        """Send email reply via SMTP with retry logic and connection pooling"""
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.config.from_name} <{self.config.email_username}>"
        msg['To'] = to_email
        msg['Subject'] = f"Re: {subject}"
        msg['In-Reply-To'] = in_reply_to
        msg['References'] = in_reply_to
        
        # Attach plain text version
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Attach HTML version if provided
        if html_body:
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Use connection pooling - reuse existing connection if available
        if not hasattr(self, '_smtp_pool') or self._smtp_pool is None:
            self._smtp_pool = []
        
        # Try to reuse existing connection from pool
        smtp_conn = None
        for conn in self._smtp_pool[:]:
            try:
                # Test if connection is still alive
                conn.noop()
                smtp_conn = conn
                self._smtp_pool.remove(conn)
                logger.debug("Reusing SMTP connection from pool")
                break
            except:
                # Connection is dead, remove it
                try:
                    conn.quit()
                except:
                    pass
                self._smtp_pool.remove(conn)
        
        try:
            if smtp_conn is None:
                # Create new connection
                context = ssl.create_default_context()
                smtp_conn = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                smtp_conn.starttls(context=context)
                smtp_conn.login(self.config.email_username, self.config.email_password)
                logger.debug("Created new SMTP connection")
            
            smtp_conn.send_message(msg)
            
            # Return connection to pool (max 3 connections)
            if len(self._smtp_pool) < 3:
                self._smtp_pool.append(smtp_conn)
            else:
                smtp_conn.quit()
            
            self.rate_limiter.record_sent()
            logger.info(f"✉️ Reply sent to {to_email}")
            return True
            
        except Exception as e:
            # Clean up failed connection
            if smtp_conn:
                try:
                    smtp_conn.quit()
                except:
                    pass
            raise e
    
    def _close_smtp_pool(self):
        """Close all pooled SMTP connections"""
        if hasattr(self, '_smtp_pool') and self._smtp_pool:
            for conn in self._smtp_pool:
                try:
                    conn.quit()
                except:
                    pass
            self._smtp_pool = []
            logger.debug("SMTP connection pool closed")
    
    def _extract_email_body(self, msg: email.message.Message) -> str:
        """Extract body from email message"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except Exception as e:
                        logger.warning(f"Failed to decode email part: {e}")
                elif content_type == 'text/html' and not body:
                    # Fallback to HTML if no plain text
                    try:
                        html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        # Simple HTML to text conversion could be added here
                        body = html
                    except Exception as e:
                        logger.warning(f"Failed to decode HTML part: {e}")
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Failed to decode email body: {e}")
        
        return body
    
    def process_single_email(self, imap: imaplib.IMAP4_SSL, email_id: bytes, mode: str) -> ProcessingResult:
        """Process a single email"""
        try:
            _, msg_data = imap.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract info
            subject = msg['subject'] or '(no subject)'
            sender = msg['from']
            msg_id = msg['message-id'] or f"generated-{email_id.decode()}"
            
            # Get body
            body = self._extract_email_body(msg)
            
            # Categorize
            category, priority, requires_escalation = self.categorize_email(subject, body, sender)
            summary = self.generate_summary(subject, body)
            
            result = ProcessingResult(
                id=email_id.decode(),
                from_addr=sender,
                subject=subject,
                category=category,
                priority=round(priority, 2),
                escalation=requires_escalation,
                summary=summary,
                action='none'
            )
            
            # Determine action
            should_reply, reason = self.should_auto_reply(category, priority, requires_escalation)
            
            if mode == 'auto' and should_reply:
                reply_body = self.generate_reply(category, subject, body)
                self.send_reply(sender, subject, reply_body, msg_id)
                result.action = 'auto_replied'
                logger.info(f"✓ Auto-replied to: {subject[:50]}...")
            elif requires_escalation:
                result.action = 'escalated'
                logger.info(f"⚠ Escalated: {subject[:50]}...")
            else:
                result.action = f'categorized ({reason})'
                logger.info(f"• Categorized: {subject[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process email {email_id}: {e}")
            return ProcessingResult(
                id=email_id.decode(),
                from_addr='',
                subject='',
                category='error',
                priority=0.0,
                escalation=True,
                summary='',
                action='error',
                error=str(e)
            )
    
    def process_emails(self, mode: str = 'monitor') -> List[ProcessingResult]:
        """Main processing loop with persistent queue and batch processing"""
        logger.info(f"Starting Inbox AI in {mode} mode...")
        
        try:
            imap = self.connect_imap()
            imap.select('INBOX')
            
            # Search for unread emails
            _, messages = imap.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            logger.info(f"Found {len(email_ids)} unread emails in inbox")
            
            # Stage 1: Queue all emails (atomic operation)
            queued_count = 0
            for email_id in email_ids:
                try:
                    _, msg_data = imap.fetch(email_id, '(RFC822)')
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    message_id = msg['message-id'] or f"generated-{email_id.decode()}"
                    sender = msg['from'] or 'unknown'
                    subject = msg['subject'] or '(no subject)'
                    body = self._extract_email_body(msg)
                    
                    if self.job_queue.add_job(
                        email_id=email_id.decode(),
                        message_id=message_id,
                        sender=sender,
                        subject=subject,
                        body=body
                    ):
                        queued_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to queue email {email_id}: {e}")
            
            logger.info(f"Queued {queued_count} new emails for processing")
            imap.close()
            imap.logout()
            
            # Stage 2: Process queued jobs with crash recovery
            self._results = []
            pending_jobs = self.job_queue.get_pending_jobs(limit=100)
            logger.info(f"Processing {len(pending_jobs)} pending jobs...")
            
            for job in pending_jobs:
                if self._shutdown:
                    logger.info("Shutdown requested, stopping processing...")
                    break
                
                self.job_queue.mark_processing(job['id'])
                
                try:
                    # Re-fetch full email from IMAP using email_id
                    imap = self.connect_imap()
                    imap.select('INBOX')
                    
                    _, msg_data = imap.fetch(job['email_id'].encode(), '(RFC822)')
                    if not msg_data or not msg_data[0]:
                        raise Exception("Email no longer available in inbox")
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    result = self._process_message(msg, job['email_id'], mode)
                    self._results.append(result)
                    
                    # Mark as completed in queue
                    self.job_queue.mark_completed(
                        job_id=job['id'],
                        result=result.action,
                        action=result.action,
                        message_id=job['message_id'],
                        category=result.category
                    )
                    
                    imap.close()
                    imap.logout()
                    
                except Exception as e:
                    logger.error(f"Failed to process job {job['id']}: {e}")
                    self.job_queue.mark_failed(job['id'], str(e))
                    
                    result = ProcessingResult(
                        id=job['email_id'],
                        from_addr=job['sender'],
                        subject=job['subject'],
                        category='error',
                        priority=0.0,
                        escalation=True,
                        summary='',
                        action='error',
                        error=str(e)
                    )
                    self._results.append(result)
            
            # Save processing log
            self._save_processing_log(mode)
            
            # Cleanup
            self._close_smtp_pool()
            
            # Log queue stats
            stats = self.job_queue.get_stats()
            logger.info(f"Queue stats: {stats}")
            
            return self._results
            
        except Exception as e:
            logger.error(f"Fatal error in processing loop: {e}", exc_info=True)
            self._close_smtp_pool()
            raise
    
    def _process_message(self, msg: email.message.Message, email_id: str, mode: str) -> ProcessingResult:
        """Process a single email message"""
        try:
            subject = msg['subject'] or '(no subject)'
            sender = msg['from']
            msg_id = msg['message-id'] or f"generated-{email_id}"
            
            body = self._extract_email_body(msg)
            category, priority, requires_escalation = self.categorize_email(subject, body, sender)
            summary = self.generate_summary(subject, body)
            
            result = ProcessingResult(
                id=email_id,
                from_addr=sender,
                subject=subject,
                category=category,
                priority=round(priority, 2),
                escalation=requires_escalation,
                summary=summary,
                action='none'
            )
            
            should_reply, reason = self.should_auto_reply(category, priority, requires_escalation)
            
            if mode == 'auto' and should_reply:
                reply_text = self.generate_reply(category, subject, body)
                html_reply = self.generate_html_reply(category, subject, body)
                self.send_reply(sender, subject, reply_text, msg_id, html_reply)
                result.action = 'auto_replied'
                logger.info(f"✓ Auto-replied to: {subject[:50]}...")
            elif requires_escalation:
                result.action = 'escalated'
                logger.info(f"⚠ Escalated: {subject[:50]}...")
            else:
                result.action = f'categorized ({reason})'
                logger.info(f"• Categorized: {subject[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            raise
    
    def _save_processing_log(self, mode: str) -> None:
        """Save processing results to log file"""
        log_dir = Path.home() / '.openclaw' / 'logs' / 'inbox-ai'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.json"
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'mode': mode,
            'total': len(self._results),
            'successful': len([r for r in self._results if not r.error]),
            'failed': len([r for r in self._results if r.error]),
            'queue_stats': self.job_queue.get_stats(),
            'emails': [
                {
                    'id': r.id,
                    'from': r.from_addr,
                    'subject': r.subject,
                    'category': r.category,
                    'priority': r.priority,
                    'action': r.action,
                    'error': r.error
                }
                for r in self._results
            ]
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        logger.info(f"Processed {len(self._results)} emails. Log: {log_file}")


def main():
    """CLI entry point"""
    mode = sys.argv[1] if len(sys.argv) > 1 else 'monitor'
    
    try:
        config = InboxProcessor.load_config()
        processor = InboxProcessor(config)
        results = processor.process_emails(mode)
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"Inbox AI Summary")
        print(f"{'='*50}")
        print(f"Total processed: {len(results)}")
        print(f"Auto-replied: {len([r for r in results if r.action == 'auto_replied'])}")
        print(f"Escalated: {len([r for r in results if r.escalation])}")
        print(f"Errors: {len([r for r in results if r.error])}")
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
