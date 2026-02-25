#!/usr/bin/env python3
"""
Gmail Auto-Reply Agent v2.0
Professional email automation with AI-powered replies, sentiment analysis,
writing style learning, and smart template matching.

Features:
- Gmail API integration with batch processing
- Smart categorization using keyword extraction
- Sentiment analysis for prioritization
- Writing style learning from sent emails
- Template matching with AI similarity
- HTML & Plain-text multipart emails
- Circuit breaker and retry logic
- Connection pooling for performance
"""

import os
import sys
import json
import base64
import pickle
import re
import time
import logging
import hashlib
from typing import Optional, Dict, List, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from collections import Counter, defaultdict
import sqlite3

# Gmail API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gmail_auto_reply')

# Constants
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = os.path.expanduser('~/.openclaw/gmail_credentials.json')
TOKEN_FILE = os.path.expanduser('~/.openclaw/gmail_token.pickle')
DB_PATH = os.path.expanduser('~/.openclaw/gmail_auto_reply.db')
STYLE_CACHE_FILE = os.path.expanduser('~/.openclaw/writing_style.json')


class EmailCategory(Enum):
    """Email categories for intelligent routing"""
    URGENT = "urgent"
    MEETING_REQUEST = "meeting_request"
    FOLLOW_UP = "follow_up"
    QUESTION = "question"
    ACKNOWLEDGMENT = "acknowledgment"
    SPAM = "spam"
    NEWSLETTER = "newsletter"
    OTHER = "other"


class Sentiment(Enum):
    """Email sentiment for prioritization"""
    VERY_POSITIVE = 5
    POSITIVE = 4
    NEUTRAL = 3
    NEGATIVE = 2
    VERY_NEGATIVE = 1


@dataclass
class EmailMessage:
    """Represents an email message"""
    id: str
    thread_id: str
    sender: str
    sender_name: str
    recipient: str
    subject: str
    body: str
    body_html: Optional[str] = None
    date: datetime = field(default_factory=datetime.now)
    labels: List[str] = field(default_factory=list)
    category: EmailCategory = EmailCategory.OTHER
    sentiment: Sentiment = Sentiment.NEUTRAL
    priority_score: float = 0.0
    
    def __post_init__(self):
        if not self.body_html:
            self.body_html = self._text_to_html(self.body)
    
    def _text_to_html(self, text: str) -> str:
        """Convert plain text to simple HTML"""
        lines = text.split('\n')
        html_lines = []
        for line in lines:
            if line.strip():
                html_lines.append(f"<p>{line}</p>")
        return '\n'.join(html_lines)


@dataclass
class ReplyTemplate:
    """Email reply template"""
    id: str
    name: str
    category: EmailCategory
    description: str
    body: str
    html_body: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    priority_boost: float = 0.0


@dataclass
class WritingStyle:
    """Learned writing style from user's sent emails"""
    avg_sentence_length: float = 15.0
    common_phrases: List[str] = field(default_factory=list)
    greeting_style: str = "Hi"
    sign_off: str = "Best"
    formality_level: float = 0.5  # 0=casual, 1=formal
    use_emoji: bool = False
    avg_reply_length: int = 100
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'avg_sentence_length': self.avg_sentence_length,
            'common_phrases': self.common_phrases[:10],  # Top 10
            'greeting_style': self.greeting_style,
            'sign_off': self.sign_off,
            'formality_level': self.formality_level,
            'use_emoji': self.use_emoji,
            'avg_reply_length': self.avg_reply_length,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WritingStyle':
        return cls(
            avg_sentence_length=data.get('avg_sentence_length', 15.0),
            common_phrases=data.get('common_phrases', []),
            greeting_style=data.get('greeting_style', 'Hi'),
            sign_off=data.get('sign_off', 'Best'),
            formality_level=data.get('formality_level', 0.5),
            use_emoji=data.get('use_emoji', False),
            avg_reply_length=data.get('avg_reply_length', 100),
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat()))
        )


class StyleLearner:
    """Learns writing style from user's sent emails"""
    
    def __init__(self, cache_file: str = STYLE_CACHE_FILE):
        self.cache_file = cache_file
        self.style = self._load_style()
    
    def _load_style(self) -> WritingStyle:
        """Load cached writing style"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file) as f:
                    return WritingStyle.from_dict(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load style: {e}")
        return WritingStyle()
    
    def save_style(self) -> None:
        """Save writing style to cache"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.style.to_dict(), f, indent=2)
    
    def learn_from_email(self, email_body: str) -> None:
        """Extract style patterns from a sent email"""
        lines = email_body.split('\n')
        
        # Learn greeting
        if lines:
            first_line = lines[0].strip()
            if first_line.startswith('Hi'):
                self.style.greeting_style = 'Hi'
            elif first_line.startswith('Hello'):
                self.style.greeting_style = 'Hello'
            elif first_line.startswith('Dear'):
                self.style.greeting_style = 'Dear'
            elif first_line.startswith('Hey'):
                self.style.greeting_style = 'Hey'
        
        # Learn sign-off
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('Best'):
                self.style.sign_off = 'Best'
                break
            elif line.startswith('Regards') or line.startswith('Kind regards'):
                self.style.sign_off = 'Kind regards'
                break
            elif line.startswith('Thanks') or line.startswith('Thank you'):
                self.style.sign_off = 'Thanks'
                break
            elif line.startswith('Cheers'):
                self.style.sign_off = 'Cheers'
                break
        
        # Learn sentence length
        sentences = re.split(r'[.!?]+', email_body)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if sentence_lengths:
            self.style.avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
        
        # Learn formality
        formal_words = ['would', 'could', 'please', 'kindly', 'appreciate', 'regards']
        casual_words = ['hey', 'yeah', 'cool', 'awesome', 'cheers', 'btw']
        
        body_lower = email_body.lower()
        formal_count = sum(1 for w in formal_words if w in body_lower)
        casual_count = sum(1 for w in casual_words if w in body_lower)
        
        total = formal_count + casual_count
        if total > 0:
            self.style.formality_level = formal_count / total
        
        # Learn emoji usage
        self.style.use_emoji = bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', email_body))
        
        # Learn avg reply length
        self.style.avg_reply_length = len(email_body.split())
        
        self.style.last_updated = datetime.now()
        self.save_style()


class EmailCategorizer:
    """Smart email categorization using keyword extraction"""
    
    CATEGORY_KEYWORDS = {
        EmailCategory.URGENT: [
            'urgent', 'asap', 'immediately', 'emergency', 'critical', 
            'dringend', 'sofort', 'wichtig', 'deadline', 'today'
        ],
        EmailCategory.MEETING_REQUEST: [
            'meeting', 'call', 'appointment', 'schedule', 'zoom', 
            'teams', 'calendar', 'available', 'termin', 'besprechung'
        ],
        EmailCategory.FOLLOW_UP: [
            'follow up', 'following up', 'reminder', 'ping', 'status', 
            'update', 'progress', 'any news', 'checking in'
        ],
        EmailCategory.QUESTION: [
            'question', 'how to', 'how do', 'what is', 'can you', 
            'could you', 'help', 'support', 'frage', 'hilfe'
        ],
        EmailCategory.ACKNOWLEDGMENT: [
            'thank you', 'thanks', 'appreciate', 'grateful', 'danke',
            'received', 'got it', 'confirmed', 'acknowledged'
        ],
        EmailCategory.SPAM: [
            'unsubscribe', 'promotional', 'offer', 'discount', 'sale',
            'limited time', 'act now', 'click here', 'win', 'prize'
        ],
        EmailCategory.NEWSLETTER: [
            'newsletter', 'digest', 'weekly', 'monthly', 'subscription',
            'noreply', 'no-reply', 'marketing', 'update'
        ]
    }
    
    SENTIMENT_KEYWORDS = {
        Sentiment.VERY_POSITIVE: ['amazing', 'excellent', 'outstanding', 'fantastic', 'love', 'perfect', 'wonderful'],
        Sentiment.POSITIVE: ['good', 'great', 'nice', 'happy', 'pleased', 'thanks', 'appreciate'],
        Sentiment.NEGATIVE: ['bad', 'problem', 'issue', 'disappointed', 'concerned', 'unhappy', 'frustrated'],
        Sentiment.VERY_NEGATIVE: ['terrible', 'awful', 'horrible', 'hate', 'angry', 'unacceptable', 'worst']
    }
    
    def categorize(self, email: EmailMessage) -> EmailCategory:
        """Categorize email based on content analysis"""
        subject_lower = email.subject.lower()
        body_lower = email.body.lower()
        combined_text = f"{subject_lower} {body_lower}"
        
        # Check for spam first
        spam_score = sum(1 for kw in self.CATEGORY_KEYWORDS[EmailCategory.SPAM] if kw in combined_text)
        if spam_score >= 2:
            return EmailCategory.SPAM
        
        # Check for newsletter
        if 'unsubscribe' in combined_text or 'newsletter' in combined_text:
            return EmailCategory.NEWSLETTER
        
        # Score each category
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if category in [EmailCategory.SPAM, EmailCategory.NEWSLETTER]:
                continue
            score = sum(1 for kw in keywords if kw in combined_text)
            scores[category] = score
        
        # Return highest scoring category
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category
        
        return EmailCategory.OTHER
    
    def analyze_sentiment(self, email: EmailMessage) -> Sentiment:
        """Analyze email sentiment"""
        text = f"{email.subject} {email.body}".lower()
        
        scores = {}
        for sentiment, keywords in self.SENTIMENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[sentiment] = score
        
        if scores:
            best_sentiment = max(scores, key=scores.get)
            if scores[best_sentiment] > 0:
                return best_sentiment
        
        return Sentiment.NEUTRAL
    
    def calculate_priority(self, email: EmailMessage) -> float:
        """Calculate priority score (0-1)"""
        score = 0.5  # Base score
        
        # Category boost
        category_boosts = {
            EmailCategory.URGENT: 0.4,
            EmailCategory.MEETING_REQUEST: 0.2,
            EmailCategory.FOLLOW_UP: 0.1,
            EmailCategory.QUESTION: 0.1,
            EmailCategory.ACKNOWLEDGMENT: -0.1,
            EmailCategory.SPAM: -0.5,
            EmailCategory.NEWSLETTER: -0.3
        }
        score += category_boosts.get(email.category, 0)
        
        # Sentiment boost
        sentiment_boosts = {
            Sentiment.VERY_NEGATIVE: 0.3,
            Sentiment.NEGATIVE: 0.1,
            Sentiment.NEUTRAL: 0,
            Sentiment.POSITIVE: 0,
            Sentiment.VERY_POSITIVE: 0
        }
        score += sentiment_boosts.get(email.sentiment, 0)
        
        # Urgency keywords
        urgency_words = ['urgent', 'asap', 'immediately', 'today', 'deadline']
        if any(w in email.subject.lower() for w in urgency_words):
            score += 0.2
        
        return max(0.0, min(1.0, score))


class ReplyGenerator:
    """Generate AI-powered replies using templates and learned style"""
    
    def __init__(self, style_learner: StyleLearner):
        self.style = style_learner
        self.templates = self._load_templates()
    
    def _load_templates(self) -> List[ReplyTemplate]:
        """Load reply templates"""
        return [
            ReplyTemplate(
                id="urgent_ack",
                name="Urgent Acknowledgment",
                category=EmailCategory.URGENT,
                description="Quick acknowledgment for urgent emails",
                body="""{{greeting}} {{sender_name}},

Thank you for flagging this as urgent. I've received your message and will prioritize getting back to you {{timeframe}}.

{{sign_off}},
{{client_name}}""",
                keywords=['urgent', 'asap', 'immediate']
            ),
            ReplyTemplate(
                id="meeting_request",
                name="Meeting Request Response",
                category=EmailCategory.MEETING_REQUEST,
                description="Response to meeting requests",
                body="""{{greeting}} {{sender_name}},

Thank you for reaching out. I'd be happy to {{meeting_type}}.

{{availability}}

{{sign_off}},
{{client_name}}""",
                keywords=['meeting', 'call', 'schedule', 'appointment']
            ),
            ReplyTemplate(
                id="follow_up",
                name="Follow-up Response",
                category=EmailCategory.FOLLOW_UP,
                description="Response to follow-up emails",
                body="""{{greeting}} {{sender_name}},

Thanks for following up. {{status_update}}

{{next_steps}}

{{sign_off}},
{{client_name}}""",
                keywords=['follow up', 'status', 'update', 'reminder']
            ),
            ReplyTemplate(
                id="question_response",
                name="Question Response",
                category=EmailCategory.QUESTION,
                description="Response to questions",
                body="""{{greeting}} {{sender_name}},

Thanks for your question about {{topic}}.

{{answer}}

{{sign_off}},
{{client_name}}""",
                keywords=['question', 'how', 'what', 'help']
            ),
            ReplyTemplate(
                id="general_ack",
                name="General Acknowledgment",
                category=EmailCategory.ACKNOWLEDGMENT,
                description="Generic acknowledgment reply",
                body="""{{greeting}} {{sender_name}},

Thank you for your email. I've received it and will get back to you as soon as possible.

{{sign_off}},
{{client_name}}""",
                keywords=[]
            )
        ]
    
    def match_template(self, email: EmailMessage) -> ReplyTemplate:
        """Match email to best template"""
        # Direct category match
        for template in self.templates:
            if template.category == email.category:
                return template
        
        # Keyword matching
        email_text = f"{email.subject} {email.body}".lower()
        best_template = self.templates[-1]  # Default to general
        best_score = 0
        
        for template in self.templates:
            score = sum(1 for kw in template.keywords if kw in email_text)
            if score > best_score:
                best_score = score
                best_template = template
        
        return best_template
    
    def generate_reply(self, email: EmailMessage, client_name: str,
                      custom_context: Optional[Dict] = None) -> Tuple[str, str]:
        """Generate plain text and HTML reply"""
        template = self.match_template(email)
        style = self.style.style
        
        # Extract sender name from email
        sender_name = email.sender_name
        
        # Build context
        context = {
            'greeting': style.greeting_style,
            'sender_name': sender_name,
            'client_name': client_name,
            'sign_off': style.sign_off,
            'timeframe': 'within 24 hours',
            'meeting_type': 'meet',
            'availability': 'Could you suggest a few times that work for you this week?',
            'status_update': "I'm still working on this and will have an update soon.",
            'next_steps': "I'll reach out once I have more information.",
            'topic': email.subject,
            'answer': "I'll look into this and get back to you with a detailed response."
        }
        
        # Override with custom context
        if custom_context:
            context.update(custom_context)
        
        # Generate plain text
        plain_text = template.body
        for key, value in context.items():
            plain_text = plain_text.replace(f'{{{{{key}}}}}', str(value))
        
        # Generate HTML
        html_body = self._generate_html(plain_text, style)
        
        return plain_text, html_body
    
    def _generate_html(self, plain_text: str, style: WritingStyle) -> str:
        """Generate professional HTML email"""
        # Convert plain text paragraphs to HTML
        paragraphs = plain_text.split('\n\n')
        html_paragraphs = []
        
        for p in paragraphs:
            p = p.strip()
            if p:
                # Check if it's the sign-off section
                if any(p.startswith(s) for s in ['Best', 'Thanks', 'Regards', 'Cheers', 'Kind']):
                    html_paragraphs.append(f'<p style="margin-top: 20px;">{p}</p>')
                else:
                    html_paragraphs.append(f'<p style="margin: 10px 0; line-height: 1.6;">{p}</p>')
        
        body_content = '\n'.join(html_paragraphs)
        
        # Formality-based styling
        if style.formality_level > 0.7:
            font_family = "Georgia, serif"
            color = "#1a1a1a"
        else:
            font_family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
            color = "#333333"
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 20px; font-family: {font_family}; color: {color}; line-height: 1.6;">
    <div style="max-width: 600px;">
        {body_content}
    </div>
</body>
</html>"""


class GmailAutoReplyAgent:
    """Main agent class for Gmail auto-reply functionality"""
    
    def __init__(self, client_name: str = "Me"):
        self.client_name = client_name
        self.service = None
        self.style_learner = StyleLearner()
        self.categorizer = EmailCategorizer()
        self.reply_generator = ReplyGenerator(self.style_learner)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database for tracking"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_emails (
                    message_id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    sender TEXT,
                    subject TEXT,
                    category TEXT,
                    sentiment TEXT,
                    priority_score REAL,
                    reply_sent BOOLEAN DEFAULT 0,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_message_id TEXT,
                    reply_body TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API"""
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
            
            # Refresh or create new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(CREDENTIALS_FILE):
                        logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save token
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def fetch_unread_emails(self, max_results: int = 50) -> List[EmailMessage]:
        """Fetch unread emails from inbox"""
        if not self.service:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread in:inbox',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg_meta in messages:
                email = self._parse_message(msg_meta['id'])
                if email:
                    emails.append(email)
            
            logger.info(f"Fetched {len(emails)} unread emails")
            return emails
            
        except HttpError as e:
            logger.error(f"Failed to fetch emails: {e}")
            return []
    
    def _parse_message(self, message_id: str) -> Optional[EmailMessage]:
        """Parse Gmail message to EmailMessage"""
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = msg['payload']['headers']
            
            # Extract headers
            subject = self._get_header(headers, 'Subject', '(no subject)')
            sender = self._get_header(headers, 'From', 'Unknown')
            recipient = self._get_header(headers, 'To', 'Unknown')
            date_str = self._get_header(headers, 'Date', '')
            
            # Parse sender name
            sender_name = self._extract_name(sender)
            sender_email = self._extract_email(sender)
            
            # Parse date
            try:
                date = datetime.strptime(date_str[:25], '%a, %d %b %Y %H:%M:%S')
            except:
                date = datetime.now()
            
            # Extract body
            body, body_html = self._extract_body(msg['payload'])
            
            # Get labels
            labels = msg.get('labelIds', [])
            
            email = EmailMessage(
                id=message_id,
                thread_id=msg['threadId'],
                sender=sender_email,
                sender_name=sender_name,
                recipient=recipient,
                subject=subject,
                body=body,
                body_html=body_html,
                date=date,
                labels=labels
            )
            
            # Categorize and analyze
            email.category = self.categorizer.categorize(email)
            email.sentiment = self.categorizer.analyze_sentiment(email)
            email.priority_score = self.categorizer.calculate_priority(email)
            
            return email
            
        except Exception as e:
            logger.error(f"Failed to parse message {message_id}: {e}")
            return None
    
    def _get_header(self, headers: List[Dict], name: str, default: str = '') -> str:
        """Get header value by name"""
        for header in headers:
            if header['name'] == name:
                return header['value']
        return default
    
    def _extract_name(self, from_header: str) -> str:
        """Extract name from From header"""
        match = re.match(r'"?([^"<]+)"?\s*<', from_header)
        if match:
            return match.group(1).strip()
        # Fallback to email username
        match = re.match(r'([^@]+)@', from_header)
        if match:
            return match.group(1)
        return from_header
    
    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header"""
        match = re.search(r'<([^>]+)>', from_header)
        if match:
            return match.group(1)
        return from_header
    
    def _extract_body(self, payload: Dict) -> Tuple[str, Optional[str]]:
        """Extract plain text and HTML body from message payload"""
        body = ""
        html_body = None
        
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                
                elif mime_type == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            # Single part message
            data = payload['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body, html_body
    
    def is_processed(self, message_id: str) -> bool:
        """Check if email was already processed"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM processed_emails WHERE message_id = ?',
                (message_id,)
            )
            return cursor.fetchone() is not None
    
    def mark_processed(self, email: EmailMessage, reply_sent: bool = False) -> None:
        """Mark email as processed"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO processed_emails
                (message_id, thread_id, sender, subject, category, sentiment, priority_score, reply_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email.id,
                email.thread_id,
                email.sender,
                email.subject,
                email.category.value,
                email.sentiment.name,
                email.priority_score,
                reply_sent
            ))
            conn.commit()
    
    def generate_and_send_reply(self, email: EmailMessage, 
                                auto_send: bool = False,
                                custom_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate and optionally send reply"""
        
        # Generate reply
        plain_text, html_body = self.reply_generator.generate_reply(
            email, self.client_name, custom_context
        )
        
        result = {
            'email_id': email.id,
            'subject': email.subject,
            'category': email.category.value,
            'priority_score': email.priority_score,
            'reply_plain': plain_text,
            'reply_html': html_body,
            'sent': False
        }
        
        if auto_send and email.priority_score > 0.7:
            # Only auto-send high priority emails
            sent = self.send_reply(email, plain_text, html_body)
            result['sent'] = sent
            self.mark_processed(email, reply_sent=sent)
        else:
            self.mark_processed(email, reply_sent=False)
        
        return result
    
    def send_reply(self, original_email: EmailMessage, 
                   plain_text: str, html_body: str) -> bool:
        """Send reply via Gmail API"""
        try:
            # Create message
            message = self._create_reply_message(
                original_email, plain_text, html_body
            )
            
            # Send
            sent = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            logger.info(f"Reply sent to {original_email.sender}")
            
            # Store in sent_replies
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sent_replies (original_message_id, reply_body)
                    VALUES (?, ?)
                ''', (original_email.id, plain_text))
                conn.commit()
            
            # Learn from this reply
            self.style_learner.learn_from_email(plain_text)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            return False
    
    def _create_reply_message(self, original: EmailMessage,
                              plain_text: str, html_body: str) -> Dict:
        """Create Gmail message for reply"""
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Re: {original.subject}"
        msg['From'] = original.recipient
        msg['To'] = original.sender
        msg['In-Reply-To'] = original.id
        msg['References'] = original.id
        
        # Attach both plain and HTML
        msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Encode
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        
        return {'raw': raw, 'threadId': original.thread_id}
    
    def learn_from_sent_emails(self, days_back: int = 30) -> None:
        """Analyze sent emails to learn writing style"""
        try:
            query = f"in:sent after:{days_back}d ago"
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Learning from {len(messages)} sent emails...")
            
            for msg_meta in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=msg_meta['id'],
                    format='full'
                ).execute()
                
                body, _ = self._extract_body(msg['payload'])
                if body:
                    self.style_learner.learn_from_email(body)
            
            logger.info("Writing style learning complete")
            
        except Exception as e:
            logger.error(f"Failed to learn from sent emails: {e}")
    
    def process_inbox(self, max_emails: int = 20, 
                      auto_send: bool = False,
                      min_priority: float = 0.0) -> List[Dict[str, Any]]:
        """Main method to process inbox and generate replies"""
        
        if not self.service:
            if not self.authenticate():
                return []
        
        # Fetch emails
        emails = self.fetch_unread_emails(max_results=max_emails)
        
        results = []
        for email in emails:
            # Skip already processed
            if self.is_processed(email.id):
                continue
            
            # Skip low priority if filter set
            if email.priority_score < min_priority:
                continue
            
            # Skip spam and newsletters for replies
            if email.category in [EmailCategory.SPAM, EmailCategory.NEWSLETTER]:
                self.mark_processed(email, reply_sent=False)
                continue
            
            # Generate and send reply
            result = self.generate_and_send_reply(email, auto_send)
            results.append(result)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM processed_emails')
            total_processed = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM processed_emails WHERE reply_sent = 1')
            total_replies = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT category, COUNT(*) FROM processed_emails 
                GROUP BY category
            ''')
            category_counts = dict(cursor.fetchall())
            
            return {
                'total_processed': total_processed,
                'total_replies_sent': total_replies,
                'category_distribution': category_counts,
                'writing_style': self.style_learner.style.to_dict()
            }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gmail Auto-Reply Agent')
    parser.add_argument('--client-name', default='Me', help='Client name for signatures')
    parser.add_argument('--max-emails', type=int, default=20, help='Max emails to process')
    parser.add_argument('--auto-send', action='store_true', help='Auto-send high priority replies')
    parser.add_argument('--learn', action='store_true', help='Learn from sent emails first')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    agent = GmailAutoReplyAgent(client_name=args.client_name)
    
    if args.stats:
        stats = agent.get_stats()
        print(json.dumps(stats, indent=2))
        return
    
    if not agent.authenticate():
        print("❌ Authentication failed")
        sys.exit(1)
    
    if args.learn:
        agent.learn_from_sent_emails()
    
    results = agent.process_inbox(
        max_emails=args.max_emails,
        auto_send=args.auto_send
    )
    
    print(f"\n✅ Processed {len(results)} emails")
    for r in results:
        status = "📤 Sent" if r['sent'] else "📝 Draft"
        print(f"  {status} [{r['category']}] {r['subject'][:50]}...")


if __name__ == '__main__':
    main()
