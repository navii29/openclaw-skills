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
    """Main email processor with improved error handling"""
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.max_auto_reply_per_hour)
        self._shutdown = False
        self._results: List[ProcessingResult] = []
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._shutdown = True
    
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
        """Generate contextual auto-reply"""
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
    
    @retry_on_error(max_retries=2, delay=2.0, exceptions=(smtplib.SMTPException, ConnectionError))
    def send_reply(self, to_email: str, subject: str, body: str, in_reply_to: str) -> bool:
        """Send email reply via SMTP with retry logic"""
        msg = MIMEMultipart()
        msg['From'] = f"{self.config.from_name} <{self.config.email_username}>"
        msg['To'] = to_email
        msg['Subject'] = f"Re: {subject}"
        msg['In-Reply-To'] = in_reply_to
        msg['References'] = in_reply_to
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        context = ssl.create_default_context()
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            server.starttls(context=context)
            server.login(self.config.email_username, self.config.email_password)
            server.send_message(msg)
        
        self.rate_limiter.record_sent()
        return True
    
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
        """Main processing loop with improved error handling"""
        logger.info(f"Starting Inbox AI in {mode} mode...")
        
        try:
            imap = self.connect_imap()
            imap.select('INBOX')
            
            # Search for unread emails
            _, messages = imap.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            logger.info(f"Found {len(email_ids)} unread emails")
            
            self._results = []
            for email_id in email_ids:
                if self._shutdown:
                    logger.info("Shutdown requested, stopping processing...")
                    break
                
                result = self.process_single_email(imap, email_id, mode)
                self._results.append(result)
            
            imap.close()
            imap.logout()
            
            # Save processing log
            log_dir = Path.home() / '.openclaw' / 'logs' / 'inbox-ai'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.json"
            
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'mode': mode,
                'total': len(self._results),
                'successful': len([r for r in self._results if not r.error]),
                'failed': len([r for r in self._results if r.error]),
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
            return self._results
            
        except Exception as e:
            logger.error(f"Fatal error in processing loop: {e}", exc_info=True)
            raise


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
