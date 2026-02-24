# Inbox AI Skill Improvement Proposal
## OpenClaw-Native Automation Migration

**Status:** Proposal  
**Priority:** High  
**Estimated Effort:** 4-6 hours  

---

## Problem Statement

Aktuell läuft Inbox AI als externes Python-Skript:
- `inbox_processor.py` muss manuell gestartet werden
- Crontab-Steuerung außerhalb von OpenClaw
- Kein Zugriff auf OpenClaw Memory/Tools
- Getrennte Fehlerbehandlung

## Proposed Solution

Migration zu OpenClaw-native Cron Jobs mit folgender Architektur:

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Cron Job: "inbox-check" (alle 5 Minuten)           │   │
│  │  - Trigger: sessions_spawn("inbox_processor")       │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │  Sub-Agent: Inbox Processor (isolated)               │  │
│  │  - Liest E-Mails via IMAP                            │  │
│  │  - Nutzt OpenClaw memory_search für Kontext          │  │
│  │  - Schreibt Ergebnisse nach memory/YYYY-MM-DD.md     │  │
│  │  - Sendet Alerts via message tool                    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. Cron Job Konfiguration

```json5
// In openclaw.json oder via CLI
{
  jobs: [
    {
      name: "inbox-check",
      schedule: { kind: "every", everyMs: 300000 }, // 5 Minuten
      payload: {
        kind: "agentTurn",
        message: "Process inbox emails. Check IMAP, categorize, reply if appropriate."
      },
      sessionTarget: "isolated",
      enabled: true,
      delivery: { mode: "announce" }
    }
  ]
}
```

Oder via CLI:
```bash
openclaw cron add \
  --name "inbox-check" \
  --every "5m" \
  --session isolated \
  --message "Process inbox emails. Check IMAP, categorize new messages, auto-reply if confidence > 0.7." \
  --model "anthropic/claude-sonnet-4-5" \
  --announce
```

### 2. Skill Definition (SKILL.md Update)

```markdown
---
name: inbox-ai-native
version: 2.0.0
description: OpenClaw-native email automation using cron jobs and sub-agents
tools:
  - exec
  - memory_search
  - memory_get
  - message
  - cron
---

# Inbox AI (OpenClaw Native)

## Setup

1. Configure email credentials:
   ```bash
   openclaw config set agents.defaults.env.IMAP_SERVER imap.ionos.de
   openclaw config set agents.defaults.env.IMAP_PORT 993
   openclaw config set agents.defaults.env.EMAIL_USERNAME kontakt@navii-automation.de
   openclaw config set agents.defaults.env.EMAIL_PASSWORD "${IONOS_EMAIL_PASSWORD}"
   ```

2. Enable cron job:
   ```bash
   openclaw cron enable inbox-check
   ```

## Operation

The cron job spawns an isolated sub-agent every 5 minutes that:
1. Connects to IMAP server
2. Fetches new unread emails
3. Uses memory_search for customer context
4. Categorizes and prioritizes
5. Generates replies if appropriate
6. Sends summary via message tool
7. Logs results to memory/
```

### 3. Python-Skript Migration

**Alt (external):**
```python
# scripts/inbox_processor.py - runs outside OpenClaw
import imaplib
# ... manual processing
```

**Neu (OpenClaw-native):**
```python
# skills/inbox-ai-native/processor.py - called via exec tool
import os
import imaplib

def process_inbox():
    # Access OpenClaw environment variables
    imap_server = os.getenv('IMAP_SERVER')
    username = os.getenv('EMAIL_USERNAME')
    
    # Use OpenClaw memory tools for context
    # (called via message/memory tools, not direct import)
    
    # Processing logic...
    
    # Return results for OpenClaw to handle
    return {
        "processed": count,
        "replied": auto_replies,
        "escalated": escalations
    }
```

### 4. Error Handling Pattern

Nutze OpenClaw's native retry und logging:

```json5
{
  agents: {
    defaults: {
      retry: {
        maxAttempts: 3,
        backoff: "exponential"
      }
    }
  }
}
```

### 5. Monitoring via Heartbeat

Erweitere HEARTBEAT.md:
```markdown
# Heartbeat Checklist

- [ ] Check inbox-cron job status: `openclaw cron runs --id inbox-check --limit 1`
- [ ] Review last email processing results in memory/today
- [ ] Alert if escalated emails > 0
- [ ] Check IMAP connection health
```

---

## Benefits

| Aspekt | Before | After |
|--------|--------|-------|
| **Setup** | Python + Cron manuell | `openclaw cron add` |
| **Monitoring** | Separate Logs | OpenClaw Logs + memory |
| **Context** | Kein Zugriff | memory_search verfügbar |
| **Fehler** | Script crashes silently | OpenClaw retry + alerts |
| **Skalierung** | 1 Instanz | Multi-agent möglich |

---

## Rollout Plan

### Phase 1: Prototyp (1 Tag)
- [ ] Neues Skill-Verzeichnis `inbox-ai-v2/`
- [ ] Basic cron job implementieren
- [ ] Test mit monitor-mode (keine Auto-Replies)

### Phase 2: Testing (2 Tage)
- [ ] Parallel zu altem System laufen lassen
- [ ] Vergleich der Ergebnisse
- [ ] Fine-tuning der Prompts

### Phase 3: Migration (1 Tag)
- [ ] Alten Cron deaktivieren
- [ ] Neuen Cron aktivieren
- [ ] Dokumentation aktualisieren

### Phase 4: Cleanup (1 Tag)
- [ ] Alte Python-Skripte archivieren
- [ ] Kunden informieren
- [ ] Support-Dokumentation anpassen

---

## Related Documentation

- `/opt/homebrew/lib/node_modules/openclaw/docs/automation/cron-jobs.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/automation/cron-vs-heartbeat.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/concepts/agent-workspace.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/tools/index.md`

---

## Decision Required

Soll diese Migration umgesetzt werden?

**Pro:** Bessere Integration, einfacheres Setup, native Monitoring  
**Contra:** Migration-Aufwand, Kunden müssen neu einrichten
