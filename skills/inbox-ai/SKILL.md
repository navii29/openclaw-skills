---
name: inbox-ai
description: Deploy 1-click AI email automation for businesses. Sorts, prioritizes, and auto-replies to emails 24/7. Use when setting up or managing intelligent inbox automation for clients including automatic categorization, prioritization, TL;DR summaries, auto-replies, and escalation handling. Supports IONOS, Gmail, and custom IMAP/SMTP providers.
---

# Inbox AI - Business Email Automation

**Version:** 2.0.0 | **Preis:** 199 EUR/Monat | **Support:** DE/EN

Complete email automation system for service businesses, executives, and support teams.

## Capabilities

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

## Supported Providers

- **IONOS** (German businesses) - See `references/ionos-setup.md`
- **Gmail** (Google Workspace) - See `references/gmail-setup.md`
- **Custom IMAP/SMTP** - Any provider with standard protocols

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

## Troubleshooting

See `references/troubleshooting.md` for common issues.
