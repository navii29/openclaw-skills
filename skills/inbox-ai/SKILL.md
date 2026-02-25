---
name: inbox-ai
description: Deploy 1-click AI email automation for businesses. Sorts, prioritizes, and auto-replies to emails 24/7. Use when setting up or managing intelligent inbox automation for clients including automatic categorization, prioritization, TL;DR summaries, auto-replies, and escalation handling. Supports IONOS, Gmail, and custom IMAP/SMTP providers.
---

# Inbox AI - Business Email Automation

**Version:** 2.2.0 | **Preis:** 199 EUR/Monat | **Support:** DE/EN

Complete email automation system for service businesses, executives, and support teams.

## Capabilities

### Core Features (v2.0)
- **Automatic Categorization** - Sorts emails by type (inquiry, support, spam, urgent)
- **Smart Prioritization** - Ranks by sender importance & urgency
- **TL;DR Summaries** - Thread summaries for quick understanding
- **Auto-Reply** - Handles 90% of emails automatically
- **Deadline & Action Detection** - Flags time-sensitive items
- **Auto-Archive** - Archives completed conversations
- **Learning** - Adapts to user's writing style
- **Escalation** - Marks complex requests for human approval
- **Multilingual** - German & English support
- **< 5min Response Time** - 24/7 availability

### v2.1.0 Self-Healing System 🆕
- **Zero-Config Onboarding** - Auto-detect email provider from address
  - Supports IONOS, Gmail, Outlook auto-detection
  - Tests connection before going live
  - No manual server configuration needed
- **Circuit Breaker** - Automatic failover on email provider issues
  - CLOSED: Normal operation
  - OPEN: Fast-fail after 5 consecutive failures
  - HALF_OPEN: Gradual recovery testing
- **Exponential Backoff** - Intelligent retry with jitter
  - Base delay: 1s, Max delay: 60s
  - Prevents thundering herd problems
  - Automatic reconnection
- **Health Monitoring** - Real-time system health score
  - IMAP/SMTP connectivity checks
  - Email processing success rate
  - Circuit breaker state monitoring
  - Uptime tracking
- **Learning Engine** - Adapts from user feedback
  - Tracks approved/rejected auto-replies
  - Sender importance scoring
  - Category accuracy improvement
  - Response time optimization

### v2.2.0 Performance & Reliability 🆕🆕
- **SMTP Connection Pooling** - Up to 70% faster mass replies
  - Reuses SMTP connections (max 3 pooled)
  - Automatic connection health checks
  - Reduced connection overhead
- **Persistent Job Queue** - Never lose an email on crash
  - SQLite-based queue with crash recovery
  - Idempotency tracking (no duplicates)
  - Automatic retry with max 3 attempts
  - Queue statistics and monitoring
- **Professional HTML Auto-Replies** - Beautiful formatted emails
  - Responsive design for mobile
  - Category-specific branded templates
  - Multipart (plain + HTML) emails
  - Professional call-to-action buttons

## Use Cases

### Use Case 1: Kundenservice-Automatisierung für E-Commerce
**Ziel:** 24/7 Verfügbarkeit für Kundenanfragen ohne zusätzliches Personal

**Szenario:** Ein Onlineshop erhält täglich 50-100 E-Mails zu Bestellstatus, Retouren und Produktfragen.

**Lösung mit Inbox AI:**
- Kategorisierung: Bestellung / Retoure / Produktfrage / Beschwerde
- Automatische Antworten mit Bestellstatus (via Shop-API)
- Eskalation von Beschwerden an Teamleiter
- TL;DR Zusammenfassungen für lange Kundenkonversationen

**Ergebnis:** 80% der Anfragen werden vollautomatisch bearbeitet, Reaktionszeit von Stunden auf Minuten reduziert.

### Use Case 2: Executive Inbox Management
**Ziel:** Wichtige E-Mails nicht übersehen, Zeitfresser eliminieren

**Szenario:** Ein Geschäftsführer erhält 200+ E-Mails täglich und verpasst kritische Nachrichten im Spam.

**Lösung mit Inbox AI:**
- Smart Prioritization: VIP-Absender werden sofort hervorgehoben
- TL;DR für lange E-Mail-Threads
- Auto-Archive für Newsletter und CC-Mails
- Telegram-Benachrichtigung für E-Mails mit Score > 0.9

**Ergebnis:** 2-3 Stunden Zeitersparnis pro Tag, keine übersehenen wichtigen E-Mails mehr.

### Use Case 3: Terminbuchung für Dienstleister
**Ziel:** Terminanfragen automatisch qualifizieren und buchen

**Szenario:** Eine Beratungsagentur erhält ständig Terminanfragen mit unterschiedlichem Kontext.

**Lösung mit Inbox AI:**
- Erkennung von Terminanfragen via KI-Kategorisierung
- Automatische Antwort mit Calendly-Link
- Qualifizierung: Budget, Zeithorizont, Dienstleistung
- Eskalation komplexer Projekte an Vertrieb

**Ergebnis:** 60% der Termine werden selbstständig gebucht, Vertrieb konzentriert sich auf qualifizierte Leads.

## Quick Start

### 1. Configure Email Provider

Copy and customize the config:

```bash
cp references/email-config.template.env ~/.openclaw/workspace/inbox-ai-config.env
# Edit with customer credentials
```

### 2. Test Connection

```bash
python3 scripts/test_email_connection.py
```

### 3. Start Processing

```bash
python3 scripts/inbox_processor.py --mode=auto
```

### v2.1.0: Zero-Config Setup (Self-Healing)
```bash
# Auto-detect and configure email provider
python3 self_healing_system.py --email user@company.de --password secret auto-config

# Check system health
python3 self_healing_system.py --email user@company.de --password secret health

# View learning statistics
python3 self_healing_system.py --email user@company.de --password secret learning-stats

# Send test email
python3 self_healing_system.py --email user@company.de --password secret \
    --to recipient@example.com --test-send
```

## Supported Providers

- **IONOS** (German businesses) - Auto-detected
- **Gmail** (Google Workspace) - Auto-detected
- **Outlook/Office365** - Auto-detected
- **Custom IMAP/SMTP** - Auto-detected from MX records

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

### Mode: `hybrid` (Approval required)
- Drafts replies for human approval
- One-click send in Telegram
- Best for: High-stakes clients

## System Prompts

The AI uses specialized prompts for different email types:

- `references/prompts/categorization.md` - Email classification
- `references/prompts/prioritization.md` - Urgency scoring
- `references/prompts/summarization.md` - TL;DR generation
- `references/prompts/auto-reply.md` - Response generation
- `references/prompts/escalation.md` - Human handoff detection

## Customer Deployment Checklist

Before going live with a customer:

- [ ] Email credentials verified (test connection)
- [ ] Sample emails analyzed (10+ examples)
- [ ] Writing style trained (past sent emails)
- [ ] Escalation contacts configured
- [ ] Auto-reply templates approved
- [ ] Customer confirmed "go live"

## Monitoring

Check processing status:

```bash
python3 scripts/stats.py --today
```

View flagged emails needing attention:

```bash
python3 scripts/list_escalated.py
```

### v2.1.0: Self-Healing System API

```python
from self_healing_system import (
    SelfHealingEmailClient, 
    ZeroConfigSetup,
    LearningEngine,
    RetryPolicy,
    CircuitBreaker
)

# Zero-Config Setup (v2.1+)
config = ZeroConfigSetup.auto_configure(
    email="kontakt@company.de",
    password="your-password"
)

if config:
    print(f"✅ Auto-configured: {config['provider'].value}")
    print(f"   IMAP: {config['imap_server']}")
    print(f"   SMTP: {config['smtp_server']}")

# v2.2+ Persistent Queue
from inbox_processor_v2 import PersistentJobQueue

queue = PersistentJobQueue()
stats = queue.get_stats()
print(f"Pending jobs: {stats.get('pending', 0)}")
print(f"Total processed: {stats.get('total_processed_ever', 0)}")

# Self-Healing Email Client
client = SelfHealingEmailClient(
    imap_server=config["imap_server"],
    imap_port=config["imap_port"],
    smtp_server=config["smtp_server"],
    smtp_port=config["smtp_port"],
    username=config["username"],
    password=config["password"],
    provider=config["provider"],
    retry_policy=RetryPolicy(
        max_retries=5,
        base_delay=1.0,
        jitter=True
    )
)

# Connect with automatic retry
if client.connect():
    print("✅ Connected with self-healing enabled")
    
    # Send email with HTML support (v2.2+)
    success = client.send_email(
        to="recipient@example.com",
        subject="Test",
        body="Hello from self-healing system!",
        html_body="<h1>Hello!</h1><p>Self-healing system is working.</p>"
    )
    
    # Check health metrics
    metrics = client.get_health_metrics()
    print(f"Health: {metrics.status} ({metrics.health_score:.0f}/100)")
    print(f"Circuit: {metrics.circuit_state}")
    print(f"Uptime: {metrics.uptime_minutes:.0f} min")
    
    client.disconnect()

# Learning Engine
engine = LearningEngine()

# Record user feedback
engine.record_feedback(
    email_id="msg123",
    sender="customer@example.com",
    category="inquiry",
    reply_text="Thank you for your inquiry...",
    approved=True,  # User approved this auto-reply
    response_time_ms=1200
)

# Get sender importance
importance = engine.get_sender_importance("vip@client.com")
print(f"Sender importance: {importance:.2f}")  # 0.0 - 1.0

# Get learning stats
stats = engine.get_learning_stats()
print(f"Approval rate: {stats['approval_rate']*100:.1f}%")
print(f"Total feedback: {stats['total_feedback']}")
```

## Troubleshooting

### Self-Healing Diagnostics

```bash
# Check system health
python3 self_healing_system.py --email user@company.de --password secret health

# Expected output:
# 📊 Health Status: 🟢 Excellent
#    Score: 95.0/100
#    IMAP: ✅
#    SMTP: ✅
#    Circuit: closed
#    Uptime: 120.5 min
```

### Circuit Breaker States

| State | Meaning | Action |
|-------|---------|--------|
| `closed` | Normal operation | Continue processing |
| `open` | 5+ failures, fast-failing | Wait 60s for recovery |
| `half_open` | Testing recovery | Limited test requests |

### Learning Engine Storage

Learning data is stored in `~/.inbox_ai/learning.db` (SQLite).

Tables:
- `feedback` - User feedback on auto-replies
- `sender_scores` - Sender importance scores
- `category_accuracy` - Classification accuracy tracking

See `references/troubleshooting.md` for common issues.
