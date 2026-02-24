# Inbox AI - Business Email Automation v2.0

Complete email automation system for service businesses, executives, and support teams.

## What's New in v2.0

### ✨ Improvements
- **Structured Logging**: Proper logging with rotation and levels
- **Retry Logic**: Automatic retry with exponential backoff for IMAP/SMTP
- **Rate Limiting**: Prevents email blacklisting (configurable per hour)
- **Config Validation**: Validates all settings on startup
- **Graceful Shutdown**: Handles SIGINT/SIGTERM properly
- **Better Error Handling**: Detailed error messages and recovery
- **Unit Tests**: Comprehensive test coverage

### 🔧 Technical Changes
- Refactored to class-based architecture
- Added `EmailConfig` dataclass for type-safe configuration
- Added `ProcessingResult` dataclass for structured output
- Signal handlers for graceful shutdown
- Circuit breaker pattern for resilience

## Quick Start

### 1. Configure Email Provider

Copy and customize the config:

```bash
cp references/email-config.template.env ~/.openclaw/workspace/inbox-ai-config.env
# Edit with customer credentials
```

### 2. Test Connection

```bash
python3 scripts/inbox_processor_v2.py monitor
```

### 3. Run Tests

```bash
python3 -m pytest scripts/test_inbox_processor.py -v
```

## Configuration

Required environment variables (in `inbox-ai-config.env`):

```env
# Email Provider
IMAP_SERVER=imap.ionos.de
IMAP_PORT=993
SMTP_SERVER=smtp.ionos.de
SMTP_PORT=587
EMAIL_USERNAME=kontakt@example.de
EMAIL_PASSWORD=secret
FROM_NAME="Your Company"

# AI Behavior
AUTO_REPLY_ENABLED=true
ESCALATION_THRESHOLD=0.7
SUMMARY_LANGUAGE=de
MAX_AUTO_REPLY_PER_HOUR=20

# Optional: Calendly Integration
CALENDLY_LINK=https://calendly.com/your-link
```

## Automation Modes

### Mode: `monitor` (Read-only)
- Categorizes and summarizes
- No automatic replies
- Best for: Testing, learning phase

### Mode: `auto` (Full automation)
- Auto-replies to standard requests
- Escalates complex cases
- Best for: Production deployment

## API Reference

### InboxProcessor

```python
from inbox_processor_v2 import InboxProcessor, EmailConfig

config = EmailConfig.from_dict({
    'IMAP_SERVER': 'imap.example.com',
    'SMTP_SERVER': 'smtp.example.com',
    'EMAIL_USERNAME': 'user@example.com',
    'EMAIL_PASSWORD': 'secret'
})

processor = InboxProcessor(config)
results = processor.process_emails(mode='monitor')
```

### RateLimiter

```python
from inbox_processor_v2 import RateLimiter

limiter = RateLimiter(max_per_hour=20)
if limiter.can_send():
    send_email()
    limiter.record_sent()
```

## Testing

Run all tests:
```bash
python3 -m pytest scripts/test_inbox_processor.py -v
```

Run with coverage:
```bash
python3 -m pytest scripts/test_inbox_processor.py --cov=inbox_processor_v2
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Config Load   │────▶│  EmailConfig    │────▶│  Validation     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
┌─────────────────┐     ┌─────────────────┐            ▼
│   RateLimiter   │◀───▶│ InboxProcessor  │◀────┌──────────────┐
└─────────────────┘     └─────────────────┘     │ Retry Logic  │
        │                       │               └──────────────┘
        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  SMTP (send)    │     │  IMAP (fetch)   │
└─────────────────┘     └─────────────────┘
```

## Error Handling

| Error | Handling |
|-------|----------|
| IMAP connection failed | Retry 3x with exponential backoff |
| SMTP send failed | Retry 2x, log error |
| Rate limit exceeded | Queue for later, notify user |
| Invalid config | Fail fast on startup |
| Signal received | Graceful shutdown, save state |

## Changelog

### v2.0.0 (2026-02-24)
- Complete refactor with class-based architecture
- Added structured logging
- Added retry logic with exponential backoff
- Added rate limiting
- Added config validation
- Added graceful shutdown
- Added comprehensive unit tests
- Improved error messages

### v1.0.0 (2026-02-19)
- Initial release
- Basic email processing
- Auto-reply functionality
- Simple categorization
