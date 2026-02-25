# Lead Pipeline Suite

**Version:** 1.0.0 | **Preis:** 149 EUR/Monat | **Bundle**

Komplette Lead-Automation: Website → CRM → Termin → Support

## Enthaltene Skills

| Skill | Version | Funktion |
|-------|---------|----------|
| website-lead-alerts | v1.0.0 | Website Lead-Erfassung |
| calendly-notion-crm | v1.0.0 | Termin-CRM Sync |
| email-slack-tickets | v1.0.0 | Support-Ticket Integration |

## Workflow

```
Website-Besucher
    ↓
🎯 Lead erfasst (Formular/Chat)
    ↓
📝 Notion CRM Eintrag
    ↓
💬 Slack Benachrichtigung
    ↓
📅 Calendly Terminbuchung
    ↓
🎫 Support-Ticket (falls nötig)
```

## Schnellstart

### Website Leads importieren
```bash
python3 suite_integration.py --website https://meinunternehmen.de/kontakt \
  --notion-token secret_xxx \
  --slack-token xoxb-xxx

# Ausgabe:
# 🌐 Website Leads importieren: https://meinunternehmen.de/kontakt
#    ✅ 2 Leads importiert
# 📝 Lead → Notion CRM...
#    ✅ Notion Page: notion-LEAD-20250225-...
# 💬 Slack Benachrichtigung...
#    ✅ Slack Thread: thread-LEAD-20250225-...
```

### Report generieren
```bash
python3 suite_integration.py --report

# Ausgabe:
# 📊 Report gespeichert: lead_pipeline_report.json
```

## Python API

```python
from suite_integration import LeadPipelineSuite, Lead

# Suite initialisieren
suite = LeadPipelineSuite(
    notion_token="secret_xxx",
    notion_database_id="xxx",
    slack_token="xoxb-xxx",
    slack_channel="#leads"
)

# Einzelnen Lead erstellen
lead = suite.create_lead(
    name="Max Mustermann",
    email="max@example.com",
    phone="+49 123 456789",
    company="Muster GmbH",
    message="Interesse an Beratung",
    priority="high",
    tags=["hot", "enterprise"]
)

# Durch Pipeline verarbeiten
result = suite.process_lead(lead)
print(result.summary())

# Website Leads importieren
leads = suite.import_website_leads("https://meinunternehmen.de/kontakt")
for lead in leads:
    suite.process_lead(lead)

# Report generieren
suite.generate_report("meine_leads.json")
```

## Einzelne Skills nutzen

### Nur Website Leads
```python
from website_leads import WebsiteLeadScraper

scraper = WebsiteLeadScraper("https://meinunternehmen.de/kontakt")
leads = scraper.scrape()
```

### Nur Notion CRM
```python
from calendly_notion import CalendlyNotionSync

sync = CalendlyNotionSync("secret_xxx", "database_xxx")
sync.sync_event_to_notion(event_data)
```

### Nur Slack Tickets
```python
from email_slack_tickets import EmailSlackIntegration

slack = EmailSlackIntegration("xoxb-xxx", "#support")
slack.create_ticket(lead_data)
```

## Installation

```bash
pip install -r website-lead-alerts/requirements.txt
pip install -r calendly-notion-crm/requirements.txt
pip install -r email-slack-tickets/requirements.txt
```

## Preisgestaltung

| Plan | Preis | Enthalten |
|------|-------|-----------|
| **Basic** | 49€/Monat | 100 Leads/Monat |
| **Professional** | 149€/Monat | 1.000 Leads, alle Features |
| **Enterprise** | 399€/Monat | Unlimited, API, Support |

## Roadmap

- [ ] LinkedIn Lead Gen Integration
- [ ] HubSpot Connector
- [ ] Automatische Lead-Scoring
- [ ] E-Mail Sequenzen
- [ ] Web-Interface
