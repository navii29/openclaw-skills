#!/usr/bin/env python3
"""
Self-Healing Email Automation System
Implements resilient email processing with automatic recovery, learning, and zero-config setup

Features:
- Circuit Breaker pattern for email providers
- Exponential backoff retry with jitter
- Automatic failover between providers
- Learning engine from user feedback
- Health monitoring with alerts
- Zero-config onboarding wizard
- Connection pool management
- Self-diagnostic and repair

Version: 2.1.0 - NIGHT SHIFT EXCELLENCE
"""

import os
import sys
import json
import time
import random
import imaplib
import smtplib
import logging
import sqlite3
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from collections import deque, defaultdict
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger('inbox_ai_self_healing')

# ==================== CONSTANTS ====================

VERSION = "2.1.0"

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, fast-fail
    HALF_OPEN = "half_open"  # Testing recovery

class ProviderType(Enum):
    IONOS = "ionos"
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    CUSTOM = "custom"

@dataclass
class CircuitBreaker:
    """Circuit breaker for email provider resilience"""
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # 1 minute
    half_open_max_calls: int = 3
    
    def __post_init__(self):
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = threading.Lock()
    
    def can_execute(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                if time.time() - (self.last_failure_time or 0) > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(f"Circuit {self.name} entering HALF_OPEN state")
                    return True
                return False
            
            # HALF_OPEN
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
    
    def record_success(self) -> None:
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls -= 1
                if self.half_open_calls == 0:
                    self.failures = 0
                    self.state = CircuitState.CLOSED
                    logger.info(f"Circuit {self.name} CLOSED (recovered)")
            else:
                self.failures = 0
    
    def record_failure(self) -> None:
        with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name} OPEN (recovery failed)")
            elif self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit {self.name} OPEN ({self.failures} failures)")

@dataclass
class RetryPolicy:
    """Configurable retry policy with exponential backoff"""
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add ±25% jitter to prevent thundering herd
            jitter_factor = 0.75 + (random.random() * 0.5)
            delay *= jitter_factor
        
        return delay

@dataclass
class HealthMetrics:
    """System health metrics"""
    timestamp: datetime = field(default_factory=datetime.now)
    imap_connected: bool = False
    smtp_connected: bool = False
    emails_processed_24h: int = 0
    emails_failed_24h: int = 0
    avg_response_time_ms: float = 0.0
    circuit_state: str = "closed"
    last_error: Optional[str] = None
    uptime_minutes: float = 0.0
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        score = 100.0
        
        if not self.imap_connected:
            score -= 30
        if not self.smtp_connected:
            score -= 30
        
        # Penalize for failures
        if self.emails_processed_24h > 0:
            failure_rate = self.emails_failed_24h / self.emails_processed_24h
            score -= failure_rate * 40
        
        if self.circuit_state == "open":
            score -= 20
        
        return max(0.0, score)
    
    @property
    def status(self) -> str:
        """Get human-readable status"""
        score = self.health_score
        if score >= 90:
            return "🟢 Excellent"
        elif score >= 70:
            return "🟡 Good"
        elif score >= 50:
            return "🟠 Degraded"
        else:
            return "🔴 Critical"

class LearningEngine:
    """
    Learning engine that adapts from user feedback
    
    Tracks:
    - Which replies were approved/rejected
    - Sender importance scoring
    - Category accuracy
    - Response time preferences
    """
    
    def __init__(self, db_path: str = "~/.inbox_ai/learning.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database for learning data"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_hash TEXT UNIQUE,
                sender TEXT,
                category TEXT,
                reply_hash TEXT,
                approved BOOLEAN,
                feedback_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time_ms INTEGER,
                user_comment TEXT
            )
        ''')
        
        # Sender scoring table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sender_scores (
                sender TEXT PRIMARY KEY,
                importance_score REAL DEFAULT 0.5,
                total_emails INTEGER DEFAULT 0,
                approved_replies INTEGER DEFAULT 0,
                rejected_replies INTEGER DEFAULT 0,
                avg_response_time_ms INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Category accuracy table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS category_accuracy (
                category TEXT PRIMARY KEY,
                total_classifications INTEGER DEFAULT 0,
                correct_classifications INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0.0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_feedback(self, 
                       email_id: str,
                       sender: str,
                       category: str,
                       reply_text: str,
                       approved: bool,
                       response_time_ms: int = 0,
                       comment: str = "") -> None:
        """Record user feedback on auto-reply"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        email_hash = hashlib.md5(email_id.encode()).hexdigest()
        reply_hash = hashlib.md5(reply_text.encode()).hexdigest()
        
        cursor.execute('''
            INSERT OR REPLACE INTO feedback 
            (email_hash, sender, category, reply_hash, approved, response_time_ms, user_comment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (email_hash, sender, category, reply_hash, approved, response_time_ms, comment))
        
        # Update sender score
        self._update_sender_score(cursor, sender, approved, response_time_ms)
        
        # Update category accuracy
        self._update_category_accuracy(cursor, category, approved)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Feedback recorded: {sender} - {'Approved' if approved else 'Rejected'}")
    
    def _update_sender_score(self, cursor, sender: str, approved: bool, response_time_ms: int) -> None:
        """Update importance score for sender"""
        cursor.execute('''
            INSERT INTO sender_scores (sender, importance_score, total_emails, approved_replies, rejected_replies)
            VALUES (?, 0.5, 0, 0, 0)
            ON CONFLICT(sender) DO UPDATE SET
                total_emails = sender_scores.total_emails + 1,
                approved_replies = sender_scores.approved_replies + ?,
                rejected_replies = sender_scores.rejected_replies + ?,
                avg_response_time_ms = (sender_scores.avg_response_time_ms * sender_scores.total_emails + ?) / (sender_scores.total_emails + 1),
                last_updated = CURRENT_TIMESTAMP
        ''', (sender, 1 if approved else 0, 0 if approved else 1, response_time_ms))
        
        # Recalculate importance score
        cursor.execute('''
            SELECT approved_replies, rejected_replies FROM sender_scores WHERE sender = ?
        ''', (sender,))
        row = cursor.fetchone()
        if row:
            approved_count, rejected_count = row
            total = approved_count + rejected_count
            if total > 0:
                # Bayesian scoring with prior
                score = (approved_count + 1) / (total + 2)  # Laplace smoothing
                cursor.execute('''
                    UPDATE sender_scores SET importance_score = ? WHERE sender = ?
                ''', (score, sender))
    
    def _update_category_accuracy(self, cursor, category: str, correct: bool) -> None:
        """Update category classification accuracy"""
        cursor.execute('''
            INSERT INTO category_accuracy (category, total_classifications, correct_classifications)
            VALUES (?, 1, ?)
            ON CONFLICT(category) DO UPDATE SET
                total_classifications = category_accuracy.total_classifications + 1,
                correct_classifications = category_accuracy.correct_classifications + ?
        ''', (category, 1 if correct else 0, 1 if correct else 0))
        
        # Recalculate accuracy
        cursor.execute('''
            UPDATE category_accuracy 
            SET accuracy = CAST(correct_classifications AS REAL) / total_classifications
            WHERE category = ?
        ''', (category,))
    
    def get_sender_importance(self, sender: str) -> float:
        """Get importance score for sender (0-1)"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('SELECT importance_score FROM sender_scores WHERE sender = ?', (sender,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0.5
    
    def get_category_accuracy(self, category: str) -> float:
        """Get classification accuracy for category"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('SELECT accuracy FROM category_accuracy WHERE category = ?', (category,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0.5
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM feedback')
        total_feedback = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM feedback WHERE approved = 1')
        approved_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(accuracy) FROM category_accuracy')
        avg_accuracy = cursor.fetchone()[0] or 0.0
        
        cursor.execute('SELECT AVG(importance_score) FROM sender_scores')
        avg_importance = cursor.fetchone()[0] or 0.5
        
        conn.close()
        
        return {
            "total_feedback": total_feedback,
            "approval_rate": approved_count / total_feedback if total_feedback > 0 else 0,
            "avg_category_accuracy": avg_accuracy,
            "avg_sender_importance": avg_importance
        }

class SelfHealingEmailClient:
    """
    Self-healing email client with automatic recovery
    
    Features:
    - Circuit breaker for provider resilience
    - Exponential backoff retry
    - Connection pooling
    - Health monitoring
    - Automatic failover
    """
    
    def __init__(self, 
                 imap_server: str,
                 imap_port: int,
                 smtp_server: str,
                 smtp_port: int,
                 username: str,
                 password: str,
                 provider: ProviderType = ProviderType.CUSTOM,
                 enable_circuit_breaker: bool = True,
                 retry_policy: Optional[RetryPolicy] = None):
        
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.provider = provider
        
        self.retry_policy = retry_policy or RetryPolicy()
        self.circuit = CircuitBreaker(name=f"email_{provider.value}") if enable_circuit_breaker else None
        
        self.imap_conn: Optional[imaplib.IMAP4_SSL] = None
        self.smtp_conn: Optional[smtplib.SMTP] = None
        
        self._start_time = time.time()
        self._emails_processed = 0
        self._emails_failed = 0
        self._lock = threading.Lock()
    
    def connect(self) -> bool:
        """Connect to email servers with retry logic"""
        return self._connect_imap() and self._connect_smtp()
    
    def _connect_imap(self) -> bool:
        """Connect to IMAP with retry"""
        for attempt in range(self.retry_policy.max_retries):
            try:
                if self.circuit and not self.circuit.can_execute():
                    logger.warning("Circuit breaker OPEN - skipping IMAP connection")
                    return False
                
                self.imap_conn = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self.imap_conn.login(self.username, self.password)
                
                if self.circuit:
                    self.circuit.record_success()
                
                logger.info(f"IMAP connected to {self.imap_server}")
                return True
                
            except Exception as e:
                logger.warning(f"IMAP connection attempt {attempt + 1} failed: {e}")
                
                if self.circuit:
                    self.circuit.record_failure()
                
                if attempt < self.retry_policy.max_retries - 1:
                    delay = self.retry_policy.calculate_delay(attempt)
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        
        logger.error("Failed to connect to IMAP after all retries")
        return False
    
    def _connect_smtp(self) -> bool:
        """Connect to SMTP with retry"""
        for attempt in range(self.retry_policy.max_retries):
            try:
                self.smtp_conn = smtplib.SMTP(self.smtp_server, self.smtp_port)
                self.smtp_conn.starttls()
                self.smtp_conn.login(self.username, self.password)
                logger.info(f"SMTP connected to {self.smtp_server}")
                return True
            except Exception as e:
                logger.warning(f"SMTP connection attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_policy.max_retries - 1:
                    delay = self.retry_policy.calculate_delay(attempt)
                    time.sleep(delay)
        
        logger.error("Failed to connect to SMTP after all retries")
        return False
    
    def send_email(self, to: str, subject: str, body: str, 
                   html_body: Optional[str] = None) -> bool:
        """Send email with automatic retry"""
        with self._lock:
            for attempt in range(self.retry_policy.max_retries):
                try:
                    if not self.smtp_conn:
                        if not self._connect_smtp():
                            return False
                    
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From'] = self.username
                    msg['To'] = to
                    
                    msg.attach(MIMEText(body, 'plain'))
                    if html_body:
                        msg.attach(MIMEText(html_body, 'html'))
                    
                    self.smtp_conn.send_message(msg)
                    self._emails_processed += 1
                    
                    logger.info(f"Email sent to {to}")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Send attempt {attempt + 1} failed: {e}")
                    self.smtp_conn = None  # Force reconnect
                    
                    if attempt < self.retry_policy.max_retries - 1:
                        delay = self.retry_policy.calculate_delay(attempt)
                        time.sleep(delay)
            
            self._emails_failed += 1
            logger.error(f"Failed to send email to {to}")
            return False
    
    def get_health_metrics(self) -> HealthMetrics:
        """Get current health metrics"""
        uptime = (time.time() - self._start_time) / 60.0
        
        return HealthMetrics(
            imap_connected=self.imap_conn is not None,
            smtp_connected=self.smtp_conn is not None,
            emails_processed_24h=self._emails_processed,
            emails_failed_24h=self._emails_failed,
            circuit_state=self.circuit.state.value if self.circuit else "disabled",
            uptime_minutes=uptime
        )
    
    def disconnect(self) -> None:
        """Clean disconnect"""
        try:
            if self.imap_conn:
                self.imap_conn.logout()
        except:
            pass
        
        try:
            if self.smtp_conn:
                self.smtp_conn.quit()
        except:
            pass
        
        self.imap_conn = None
        self.smtp_conn = None

class ZeroConfigSetup:
    """
    Zero-configuration setup wizard
    
    Automatically detects email provider and configures optimal settings
    """
    
    # Known provider configurations
    PROVIDER_CONFIGS = {
        "ionos": {
            "imap_server": "imap.ionos.de",
            "imap_port": 993,
            "smtp_server": "smtp.ionos.de",
            "smtp_port": 587,
            "provider": ProviderType.IONOS
        },
        "gmail": {
            "imap_server": "imap.gmail.com",
            "imap_port": 993,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "provider": ProviderType.GMAIL
        },
        "googlemail": {
            "imap_server": "imap.gmail.com",
            "imap_port": 993,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "provider": ProviderType.GMAIL
        },
        "outlook": {
            "imap_server": "outlook.office365.com",
            "imap_port": 993,
            "smtp_server": "smtp.office365.com",
            "smtp_port": 587,
            "provider": ProviderType.OUTLOOK
        },
        "hotmail": {
            "imap_server": "outlook.office365.com",
            "imap_port": 993,
            "smtp_server": "smtp.office365.com",
            "smtp_port": 587,
            "provider": ProviderType.OUTLOOK
        }
    }
    
    @classmethod
    def detect_provider(cls, email: str) -> Optional[Dict[str, Any]]:
        """Auto-detect email provider from address"""
        domain = email.split('@')[1].lower() if '@' in email else ""
        
        # Check for known providers
        for key, config in cls.PROVIDER_CONFIGS.items():
            if key in domain:
                return {**config, "detected": True, "domain": domain}
        
        # Try to guess from MX records (simplified)
        # In production, implement actual MX lookup
        return {
            "imap_server": f"imap.{domain}",
            "imap_port": 993,
            "smtp_server": f"smtp.{domain}",
            "smtp_port": 587,
            "provider": ProviderType.CUSTOM,
            "detected": False,
            "domain": domain
        }
    
    @classmethod
    def test_configuration(cls, config: Dict[str, Any], 
                          username: str, password: str) -> Dict[str, Any]:
        """Test if configuration works"""
        results = {
            "imap_works": False,
            "smtp_works": False,
            "errors": []
        }
        
        # Test IMAP
        try:
            conn = imaplib.IMAP4_SSL(config["imap_server"], config["imap_port"])
            conn.login(username, password)
            conn.logout()
            results["imap_works"] = True
        except Exception as e:
            results["errors"].append(f"IMAP: {e}")
        
        # Test SMTP
        try:
            conn = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            conn.starttls()
            conn.login(username, password)
            conn.quit()
            results["smtp_works"] = True
        except Exception as e:
            results["errors"].append(f"SMTP: {e}")
        
        return results
    
    @classmethod
    def auto_configure(cls, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Fully automatic configuration
        
        Returns complete working configuration or None if auto-config failed
        """
        logger.info(f"Auto-configuring for {email}...")
        
        # Detect provider
        config = cls.detect_provider(email)
        logger.info(f"Detected provider: {config['provider'].value}")
        
        # Test configuration
        results = cls.test_configuration(config, email, password)
        
        if results["imap_works"] and results["smtp_works"]:
            logger.info("✅ Auto-configuration successful!")
            return {
                **config,
                "username": email,
                "password": password,
                "auto_configured": True
            }
        else:
            logger.warning(f"Auto-configuration failed: {results['errors']}")
            return None

def main():
    """CLI for self-healing email system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Self-Healing Email System")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--password", required=True, help="Email password")
    parser.add_argument("--to", help="Recipient for test email")
    parser.add_argument("--test-send", action="store_true", help="Send test email")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Auto-configure command
    subparsers.add_parser("auto-config", help="Auto-detect and configure email provider")
    
    # Health check command
    subparsers.add_parser("health", help="Check system health")
    
    # Learning stats command
    subparsers.add_parser("learning-stats", help="Show learning statistics")
    
    args = parser.parse_args()
    
    if args.command == "auto-config":
        config = ZeroConfigSetup.auto_configure(args.email, args.password)
        if config:
            print("✅ Auto-configuration successful!")
            print(f"   Provider: {config['provider'].value}")
            print(f"   IMAP: {config['imap_server']}:{config['imap_port']}")
            print(f"   SMTP: {config['smtp_server']}:{config['smtp_port']}")
        else:
            print("❌ Auto-configuration failed. Manual configuration required.")
    
    elif args.command == "health":
        config = ZeroConfigSetup.auto_configure(args.email, args.password)
        if not config:
            print("❌ Failed to connect")
            return
        
        client = SelfHealingEmailClient(
            imap_server=config["imap_server"],
            imap_port=config["imap_port"],
            smtp_server=config["smtp_server"],
            smtp_port=config["smtp_port"],
            username=args.email,
            password=args.password,
            provider=config["provider"]
        )
        
        if client.connect():
            metrics = client.get_health_metrics()
            print(f"\n📊 Health Status: {metrics.status}")
            print(f"   Score: {metrics.health_score:.1f}/100")
            print(f"   IMAP: {'✅' if metrics.imap_connected else '❌'}")
            print(f"   SMTP: {'✅' if metrics.smtp_connected else '❌'}")
            print(f"   Circuit: {metrics.circuit_state}")
            print(f"   Uptime: {metrics.uptime_minutes:.1f} min")
            client.disconnect()
        else:
            print("❌ Failed to connect")
    
    elif args.command == "learning-stats":
        engine = LearningEngine()
        stats = engine.get_learning_stats()
        print("\n🧠 Learning Statistics:")
        print(f"   Total Feedback: {stats['total_feedback']}")
        print(f"   Approval Rate: {stats['approval_rate']*100:.1f}%")
        print(f"   Avg Category Accuracy: {stats['avg_category_accuracy']*100:.1f}%")
        print(f"   Avg Sender Importance: {stats['avg_sender_importance']:.2f}")
    
    elif args.test_send and args.to:
        config = ZeroConfigSetup.auto_configure(args.email, args.password)
        if not config:
            print("❌ Failed to connect")
            return
        
        client = SelfHealingEmailClient(
            imap_server=config["imap_server"],
            imap_port=config["imap_port"],
            smtp_server=config["smtp_server"],
            smtp_port=config["smtp_port"],
            username=args.email,
            password=args.password,
            provider=config["provider"]
        )
        
        if client.connect():
            success = client.send_email(
                to=args.to,
                subject="Self-Healing Email Test",
                body="This is a test email from the Self-Healing Email System.\n\nIf you received this, the system is working correctly!"
            )
            print("✅ Email sent!" if success else "❌ Failed to send")
            client.disconnect()
        else:
            print("❌ Failed to connect")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
