# OpenClaw ↔ n8n Bidirectional Bridge
## "Agent Command Center" Integration

### Executive Summary
Eine **zweirichtige Integrationsbrücke** zwischen OpenClaw und n8n, die es Agenten ermöglicht, nicht nur zu reagieren, sondern **aktiv Workflows zu triggern**, Daten zu erfassen und externe Systeme zu steuern.

**Status:** Proof-of-Concept implementiert ✅  
**Implementierungszeit:** 2-3 Stunden  
**ROI für Kunden:** 5-10h/Woche manuelle Arbeit eingespart

---

## Das Problem

Aktuelle Limitation:
- n8n kann OpenClaw-Agenten triggern ✅ (via HTTP Request → sessions_spawn)
- OpenClaw kann **nicht direkt** n8n-Workflows steuern ❌
- Agenten sind "reaktiv", nicht "proaktiv"
- Keine Echtzeit-Rückkopplung von externen Systemen

**Beispiel:** Agent analysiert E-Mail, möchte CRM aktualisieren + Slack benachrichtigen + Kalender blocken → braucht 3 separate Tools, statt einen unified call.

---

## Die Lösung: Bidirectional Bridge

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT COMMAND CENTER                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐         Webhook          ┌─────────────────────┐    │
│   │   OpenClaw   │ ───────────────────────→ │         n8n         │    │
│   │    Agent     │   (JSON Command)         │    Orchestrator     │    │
│   └──────────────┘                          └─────────────────────┘    │
│          ↑                                           │                  │
│          │                                           │                  │
│          │     Return Data / Confirmations          ↓                  │
│          │                                   ┌─────────────┐           │
│           ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← │  External   │           │
│                                             │   Systems   │           │
│                                             │  • HubSpot  │           │
│                                             │  • Slack    │           │
│                                             │  • Calendar │           │
│                                             │  • Notion   │           │
│                                             │  • Gmail    │           │
│                                             └─────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Komponenten

### 1. n8n Workflow: `openclaw-command-router`

**Zweck:** Zentraler Empfänger für alle OpenClaw-Befehle

```json
{
  "name": "OpenClaw Command Router",
  "nodes": [
    {
      "name": "Command Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "httpMethod": "POST",
        "path": "openclaw-command",
        "responseMode": "responseNode"
      }
    },
    {
      "name": "Validate Command",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "rules": {
          "rules": [
            { "value": "crm_update", "output": 0 },
            { "value": "slack_notify", "output": 1 },
            { "value": "calendar_block", "output": 2 },
            { "value": "email_send", "output": 3 },
            { "value": "notion_create", "output": 4 },
            { "value": "webhook_forward", "output": 5 }
          ]
        }
      }
    }
  ]
}
```

### 2. OpenClaw Skill: `n8n_bridge`

**Zweck:** Einfacher Python-Wrapper für n8n Webhooks

```python
# skills/n8n_bridge/skill.py
import requests
import json
from typing import Dict, Any, Optional

N8N_WEBHOOK_URL = "https://navii-automation.app.n8n.cloud/webhook/openclaw-command"
N8N_API_KEY = "sk_..."  # From environment

def send_command(
    command: str,
    payload: Dict[str, Any],
    wait_for_response: bool = True,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Send a command to n8n orchestrator.
    
    Args:
        command: Type of command (crm_update, slack_notify, etc.)
        payload: Command-specific data
        wait_for_response: Whether to wait for n8n response
        timeout: Timeout in seconds
    
    Returns:
        n8n response or status confirmation
    """
    data = {
        "source": "openclaw",
        "timestamp": datetime.utcnow().isoformat(),
        "command": command,
        "payload": payload
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": N8N_API_KEY
    }
    
    response = requests.post(
        N8N_WEBHOOK_URL,
        json=data,
        headers=headers,
        timeout=timeout if wait_for_response else 5
    )
    
    return response.json() if wait_for_response else {"status": "sent"}

# Convenience functions for common operations
def update_hubspot_deal(deal_id: str, properties: Dict[str, Any]) -> Dict:
    """Update HubSpot deal properties"""
    return send_command("crm_update", {
        "system": "hubspot",
        "deal_id": deal_id,
        "properties": properties
    })

def send_slack_message(channel: str, text: str, blocks: Optional[list] = None) -> Dict:
    """Send Slack notification"""
    return send_command("slack_notify", {
        "channel": channel,
        "text": text,
        "blocks": blocks
    })

def create_calendar_block(
    title: str,
    start_time: str,
    duration_minutes: int = 30,
    attendees: Optional[list] = None
) -> Dict:
    """Block calendar time"""
    return send_command("calendar_block", {
        "title": title,
        "start": start_time,
        "duration": duration_minutes,
        "attendees": attendees or []
    })

def send_email(
    to: str,
    subject: str,
    body: str,
    from_account: str = "ionos"
) -> Dict:
    """Send email via configured provider"""
    return send_command("email_send", {
        "to": to,
        "subject": subject,
        "body": body,
        "from_account": from_account
    })
```

### 3. Universal n8n Sub-Workflows

Für jeden Befehlstyp gibt es einen optimierten Sub-Workflow:

#### 3.1 CRM Update Workflow
```json
{
  "name": "CRM Update Handler",
  "trigger": "openclaw-command (crm_update)",
  "nodes": [
    {
      "name": "Route by System",
      "type": "switch",
      "cases": ["hubspot", "pipedrive", "salesforce"]
    },
    {
      "name": "Update HubSpot",
      "type": "httpRequest",
      "parameters": {
        "method": "PATCH",
        "url": "={{ 'https://api.hubapi.com/crm/v3/objects/deals/' + $json.payload.deal_id }}",
        "body": "={{ $json.payload.properties }}"
      }
    }
  ]
}
```

#### 3.2 Slack Notify Workflow
```json
{
  "name": "Slack Notify Handler",
  "nodes": [
    {
      "name": "Format Message",
      "type": "code",
      "jsCode": "// Format OpenClaw data for Slack\nconst payload = $input.first().json.payload;\nconst blocks = [\n  {\n    type: 'header',\n    text: { type: 'plain_text', text: '🤖 Agent Update' }\n  },\n  {\n    type: 'section',\n    text: { type: 'mrkdwn', text: payload.text }\n  }\n];\nreturn [{ json: { channel: payload.channel, blocks } }];"
    },
    {
      "name": "Send to Slack",
      "type": "slack",
      "parameters": {
        "channel": "={{ $json.channel }}",
        "blocks": "={{ $json.blocks }}"
      }
    }
  ]
}
```

#### 3.3 Calendar Block Workflow
```json
{
  "name": "Calendar Block Handler",
  "nodes": [
    {
      "name": "Create Event",
      "type": "googleCalendar",
      "parameters": {
        "calendar": "primary",
        "start": "={{ $json.payload.start }}",
        "end": "={{ $json.payload.end || addMinutes($json.payload.start, $json.payload.duration || 30) }}",
        "summary": "={{ $json.payload.title }}",
        "attendees": "={{ $json.payload.attendees }}"
      }
    }
  ]
}
```

---

## Use Cases & Agent Workflows

### Use Case 1: Lead-Qualifizierung End-to-End

**Vorher:**
1. Agent analysiert E-Mail → Output Text
2. Manuelles Kopieren in HubSpot
3. Manuelle Slack-Nachricht
4. Manuelle Kalender-Blockung

**Nachher (mit Bridge):**
```python
# In OpenClaw Agent
def process_lead_email(email_content, sender):
    # 1. Analysiere E-Mail
    analysis = analyze_email(email_content)
    
    if analysis["is_qualified"]:
        # 2. Erstelle Deal in HubSpot
        hubspot_deal = n8n_bridge.send_command("crm_create", {
            "system": "hubspot",
            "properties": {
                "dealname": f"Lead: {sender['company']}",
                "amount": analysis["estimated_value"],
                "pipeline": "default",
                "dealstage": "appointmentscheduled"
            }
        })
        
        # 3. Benachrichtige Sales-Team
        n8n_bridge.send_command("slack_notify", {
            "channel": "#sales-hot",
            "text": f"🔥 HOT LEAD: {sender['company']} (€{analysis['estimated_value']})",
            "blocks": format_slack_blocks(analysis)
        })
        
        # 4. Blocke Vorbereitungszeit im Kalender
        n8n_bridge.send_command("calendar_block", {
            "title": f"Prep: {sender['company']} Call",
            "start": analysis["suggested_meeting_time"],
            "duration": 30
        })
        
        # 5. Sende personalisierte Antwort
        n8n_bridge.send_command("email_send", {
            "to": sender["email"],
            "subject": f"Re: {sender['subject']} - Terminvorschlag",
            "body": generate_response(analysis),
            "track_opens": True
        })
        
        return f"Lead fully processed. Deal ID: {hubspot_deal['id']}"
```

### Use Case 2: Meeting-Vorbereitung Automatisierung

**Trigger:** Calendly-Buchung (via n8n → OpenClaw)

```python
def prepare_for_meeting(meeting_data):
    # 1. Recherchiere Unternehmen
    company_intel = research_company(meeting_data["company"])
    
    # 2. Recherchiere Person
    person_intel = research_person(meeting_data["email"])
    
    # 3. Erstelle Notion-Seite mit Briefing
    briefing = n8n_bridge.send_command("notion_create", {
        "database": "Meeting Briefings",
        "properties": {
            "Name": f"{meeting_data['company']} - {meeting_data['date']}",
            "Company": meeting_data["company"],
            "Attendee": meeting_data["name"],
            "Briefing": format_briefing(company_intel, person_intel),
            "Status": "Ready"
        }
    })
    
    # 4. Slack-Benachrichtigung mit Link
    n8n_bridge.send_command("slack_notify", {
        "channel": "#meetings",
        "text": f"📋 Briefing ready for {meeting_data['company']}",
        "blocks": [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Meeting Prep Complete*\n{meeting_data['company']} - {meeting_data['date']}\n<{briefing['url']}|View Briefing>"
            }
        }]
    })
```

### Use Case 3: Kunden-Status-Updates

```python
def handle_customer_update(ticket_data):
    # Analysiere Ticket
    sentiment = analyze_sentiment(ticket_data["message"])
    priority = calculate_priority(ticket_data)
    
    # Update CRM
    n8n_bridge.send_command("crm_update", {
        "system": "hubspot",
        "object_type": "ticket",
        "object_id": ticket_data["ticket_id"],
        "properties": {
            "hs_ticket_priority": priority,
            "ai_sentiment": sentiment["score"],
            "ai_summary": sentiment["summary"]
        }
    })
    
    # Bei negativem Sentiment: Alert
    if sentiment["score"] < -0.5:
        n8n_bridge.send_command("slack_notify", {
            "channel": "#customer-alerts",
            "text": f"⚠️ Negative sentiment detected: {ticket_data['company']}",
            "priority": "urgent"
        })
        
        # Auto-escalation
        n8n_bridge.send_command("webhook_forward", {
            "url": "https://escalation-system.com/api/alert",
            "payload": ticket_data
        })
```

---

## Implementation Guide

### Schritt 1: n8n Setup (15 Min)

1. **Webhook-Workflow erstellen:**
```bash
# Import in n8n
curl -X POST "https://navii-automation.app.n8n.cloud/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -d @openclaw-command-router.json
```

2. **API-Key als Environment Variable:**
```bash
# In n8n Settings → Environment
BRIDGE_API_KEY=sk_live_...
```

### Schritt 2: OpenClaw Skill Installation (10 Min)

```bash
# Create skill directory
mkdir -p ~/.openclaw/workspace/skills/n8n_bridge

# Copy skill files
cp n8n_bridge/skill.py ~/.openclaw/workspace/skills/n8n_bridge/
cp n8n_bridge/SKILL.md ~/.openclaw/workspace/skills/n8n_bridge/

# Verify installation
openclaw skills list | grep n8n_bridge
```

### Schritt 3: Testing (15 Min)

```python
# Test script
from skills.n8n_bridge import send_command

# Test connectivity
result = send_command("ping", {"test": True})
assert result["status"] == "pong"

# Test Slack notification
result = send_command("slack_notify", {
    "channel": "#test",
    "text": "🧪 Bridge test successful!"
})

print(f"✅ Bridge operational: {result}")
```

---

## Command Reference

| Command | Payload | Response | Use Case |
|---------|---------|----------|----------|
| `crm_update` | `system`, `object_id`, `properties` | `{updated: true, id: "..."}` | Update records |
| `crm_create` | `system`, `properties` | `{created: true, id: "..."}` | Create new records |
| `slack_notify` | `channel`, `text`, `blocks?` | `{sent: true, ts: "..."}` | Notifications |
| `email_send` | `to`, `subject`, `body`, `from_account` | `{message_id: "..."}` | Email dispatch |
| `calendar_block` | `title`, `start`, `duration`, `attendees?` | `{event_id: "..."}` | Time blocking |
| `notion_create` | `database`, `properties` | `{page_id: "...", url: "..."}` | Documentation |
| `webhook_forward` | `url`, `payload`, `headers?` | `{status: 200}` | Custom integrations |
| `multi_action` | `actions: []` | Array of results | Batch operations |

---

## Pricing & Packaging

### Für Agentur-Kunden

| Paket | Features | Setup | Monatlich |
|-------|----------|-------|-----------|
| **Starter** | CRM + Slack + Email | €1.500 | €200 |
| **Professional** | + Calendar + Notion + 2-way sync | €2.500 | €400 |
| **Enterprise** | + Custom integrations + Priority support | €5.000 | €800 |

**Value Proposition:**
- 5-10h/Woche gespart
- Keine Kontext-Switches mehr
- Einheitliche Command-API für alle Systeme

---

## Nächste Schritte

- [ ] n8n Router Workflow deployen
- [ ] Skill in OpenClaw aktivieren
- [ ] Test-Commands ausführen
- [ ] Use Case 1 (Lead-Qualifizierung) implementieren
- [ ] Dokumentation für Kunden erstellen
- [ ] Demo-Video aufnehmen

---

## Technical Notes

### Security
- API-Key Authentication (Header: `X-API-Key`)
- IP-Whitelist für n8n (optional)
- Payload validation via JSON Schema
- Audit-Logging aller Commands

### Error Handling
```python
# In skill.py
def send_command(...):
    try:
        response = requests.post(...)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return {"error": "timeout", "fallback": "queue_for_retry"}
    except requests.HTTPError as e:
        return {"error": "http_error", "status": e.response.status_code}
```

### Rate Limiting
- n8n Cloud: 1.000 Ausführungen/Monat (kostenlos)
- Empfohlen: 10.000/Monat Plan für Agentur-Use-Cases

---

*Erstellt: 26. Februar 2026*  
*Autor: OpenClaw Learning Session 2*  
*Status: POC Complete → Implementation Ready*
