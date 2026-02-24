# Pattern Migration: Inbox AI vorher → nachher

**Konkrete Migration eines bestehenden OpenClaw Skills zu Advanced Patterns**

---

## Aktueller Zustand (Vorher)

```
skills/inbox-ai/
├── scripts/
│   ├── inbox_processor.py      # 500 Zeilen, alles in einem
│   ├── categorizer.py          # Direkte API Calls
│   └── responder.py            # Syncron IMAP
├── config/
│   └── settings.env            # Statische Config
└── data/
    └── emails.db               # SQLite, lokal
```

### Probleme
1. **Monolithisch**: Ein Skript macht alles
2. **Synchrone I/O**: Blockiert bei jedem API Call
3. **Keine Retry-Logik**: Fehler = Datenverlust
4. **Schwer testbar**: Enge Kopplung
5. **Nicht skalierbar**: Keine Parallelisierung

### Code (vorher)
```python
# scripts/inbox_processor.py - MONOLITH
import imaplib
import sqlite3

def process_inbox():
    # 1. Connect IMAP
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(EMAIL, PASSWORD)
    
    # 2. Fetch emails
    _, messages = mail.search(None, 'UNSEEN')
    
    for msg_id in messages[0].split():
        # 3. Extract (blocking)
        email_data = extract_email(mail, msg_id)
        
        # 4. Categorize (blocking AI call)
        category = ai_categorize(email_data)
        
        # 5. Save to DB (blocking)
        save_to_sqlite(email_data, category)
        
        # 6. Route (blocking)
        if category == 'lead':
            send_to_hubspot(email_data)  # Kann fehlen!
        
        # Keine Compensation!
        # Wenn HubSpot fehlschlägt, ist Email als "processed" markiert
        # aber nicht in HubSpot
```

---

## Zielzustand (Nachher)

```
skills/inbox-ai-v2/
├── events/                      # EDA
│   ├── schemas/
│   │   ├── EmailReceived.json
│   │   ├── EmailCategorized.json
│   │   └── EmailRouted.json
│   └── handlers/
│       ├── on_email_received.py
│       ├── on_email_categorized.py
│       └── on_email_routed.py
├── commands/                    # CQRS - Write Side
│   ├── extract_email.py
│   ├── categorize_email.py
│   └── route_email.py
├── queries/                     # CQRS - Read Side
│   ├── get_inbox_summary.py
│   ├── search_emails.py
│   └── get_email_detail.py
├── projections/                 # CQRS - Projections
│   ├── inbox_projector.py
│   └── search_index_updater.py
├── sagas/                       # Saga Pattern
│   ├── email-processing.yaml
│   └── orchestrator.py
├── infrastructure/
│   ├── event_bus.py
│   ├── command_dispatcher.py
│   └── saga_store.py
└── config/
    ├── cron-jobs.json           # OpenClaw Cron
    └── skill-manifest.yaml
```

---

## Schritt-für-Schritt Migration

### Phase 1: Event-Driven Architecture einführen

#### 1.1 Event Schemas definieren
```json
// events/schemas/EmailReceived.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["eventId", "eventType", "timestamp", "payload"],
  "properties": {
    "eventId": {"type": "string", "format": "uuid"},
    "eventType": {"type": "string", "const": "email.received"},
    "timestamp": {"type": "string", "format": "date-time"},
    "source": {"type": "string", "const": "inbox-emitter"},
    "correlationId": {"type": "string", "format": "uuid"},
    "payload": {
      "type": "object",
      "properties": {
        "emailId": {"type": "string"},
        "subject": {"type": "string"},
        "sender": {"type": "string"},
        "receivedAt": {"type": "string", "format": "date-time"},
        "rawContent": {"type": "string"}
      }
    }
  }
}
```

#### 1.2 Event Emitter (Cron Job)
```python
# infrastructure/event_emitter.py
# Wird jede 5 Minuten via OpenClaw Cron aufgerufen

import json
from datetime import datetime

def emit_email_events():
    """
    Prüft Inbox und emitted Events für neue Emails.
    Nutzt OpenClaw exec für IMAP-Zugriff.
    """
    # IMAP Check
    result = exec(
        command="python3 scripts/check_inbox.py --json-output",
        timeout=30
    )
    
    emails = json.loads(result.output)
    
    for email in emails:
        # Event erstellen
        event = {
            "eventId": str(uuid.uuid4()),
            "eventType": "email.received",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "inbox-emitter",
            "correlationId": str(uuid.uuid4()),
            "payload": email
        }
        
        # Event speichern (Event Store)
        write_file(
            path=f"memory/events/email-received/{event['eventId']}.json",
            content=json.dumps(event, indent=2)
        )
        
        # Mark as unprocessed for handlers
        write_file(
            path=f"memory/events/unprocessed/{event['eventId']}.json",
            content=json.dumps({
                "eventId": event['eventId'],
                "eventType": event['eventType'],
                "status": "pending",
                "retryCount": 0
            })
        )
    
    return {"emitted": len(emails)}
```

#### 1.3 OpenClaw Cron Job
```json
{
  "name": "inbox-event-emitter",
  "schedule": {"kind": "every", "everyMs": 300000},
  "payload": {
    "kind": "agentTurn",
    "message": "Run infrastructure/event_emitter.py to check inbox and emit email.received events for each new email",
    "model": "kimi-coding/k2p5"
  },
  "sessionTarget": "isolated",
  "delivery": {"mode": "none"}
}
```

#### 1.4 Event Handler
```python
# events/handlers/on_email_received.py

def handle(event_data):
    """
    Handler für email.received Events.
    Startet eine neue Saga für diese Email.
    """
    email_id = event_data['payload']['emailId']
    correlation_id = event_data['correlationId']
    
    # Saga starten
    saga = EmailProcessingSaga(
        saga_id=correlation_id,
        email_id=email_id,
        event_data=event_data['payload']
    )
    
    # Saga State speichern
    write_file(
        path=f"memory/sagas/active/{correlation_id}.json",
        content=json.dumps(saga.to_dict(), indent=2)
    )
    
    # Nächsten Schritt triggern (Categorize)
    sessions_spawn(
        task=f"Execute saga step 'categorize' for {email_id}",
        agentId="categorizer-agent",
        timeoutSeconds=60
    )
```

---

### Phase 2: CQRS implementieren

#### 2.1 Commands (Write Side)
```python
# commands/extract_email.py

class ExtractEmailCommand:
    def __init__(self, email_id, imap_config):
        self.command_id = str(uuid.uuid4())
        self.email_id = email_id
        self.imap_config = imap_config
        self.timestamp = datetime.utcnow().isoformat()

class ExtractEmailHandler:
    def handle(self, command: ExtractEmailCommand):
        # IMAP Extraktion
        email_data = self._fetch_from_imap(command.email_id)
        
        # Event generieren
        event = {
            "eventType": "email.extracted",
            "payload": {
                "emailId": command.email_id,
                "content": email_data,
                "extractedAt": datetime.utcnow().isoformat()
            },
            "correlationId": command.email_id
        }
        
        # Aggregate aktualisieren (Write Model)
        self._update_aggregate(command.email_id, {
            "status": "extracted",
            "version": 1
        })
        
        return event
    
    def _fetch_from_imap(self, email_id):
        # Nutzt OpenClaw exec
        result = exec(
            command=f"python3 scripts/fetch_email.py {email_id}",
            timeout=30
        )
        return json.loads(result.output)
    
    def _update_aggregate(self, email_id, data):
        path = f"memory/aggregates/emails/{email_id}.json"
        write_file(path, json.dumps(data, indent=2))
```

```python
# commands/categorize_email.py

class CategorizeEmailCommand:
    def __init__(self, email_id, content):
        self.command_id = str(uuid.uuid4())
        self.email_id = email_id
        self.content = content

class CategorizeEmailHandler:
    def handle(self, command: CategorizeEmailCommand):
        # AI Categorization via sessions_spawn
        result = sessions_spawn(
            task=f"Categorize this email: {command.content[:500]}...",
            agentId="categorizer-v2",
            timeoutSeconds=60
        )
        
        category = self._parse_category(result)
        
        # Event generieren
        event = {
            "eventType": "email.categorized",
            "payload": {
                "emailId": command.email_id,
                "category": category,
                "confidence": result.get("confidence", 0.8),
                "categorizedAt": datetime.utcnow().isoformat()
            },
            "correlationId": command.email_id
        }
        
        # Aggregate aktualisieren
        self._update_aggregate(command.email_id, {
            "status": "categorized",
            "category": category,
            "version": 2
        })
        
        return event
```

#### 2.2 Queries (Read Side)
```python
# queries/get_inbox_summary.py

def get_inbox_summary():
    """
    Optimierte Query - nutzt memory_search
    """
    # Suche über den Search Index (schnell)
    unread_high = memory_search(
        query="eventType:email.categorized priority:HIGH status:unread",
        maxResults=100
    )
    
    unread_medium = memory_search(
        query="eventType:email.categorized priority:MEDIUM status:unread",
        maxResults=100
    )
    
    # Aggregierte Stats
    return {
        "counts": {
            "high": len(unread_high.results),
            "medium": len(unread_medium.results),
            "total": len(unread_high.results) + len(unread_medium.results)
        },
        "requiresAttention": len(unread_high.results) > 0,
        "lastUpdated": datetime.utcnow().isoformat()
    }


def get_email_detail(email_id):
    """
    Direkte Aggregate-Abfrage
    """
    return read_file(f"memory/aggregates/emails/{email_id}.json")
```

#### 2.3 Projections (Event → Read Model)
```python
# projections/inbox_projector.py

class InboxProjector:
    """
    Projiziert Events auf Read Models (Views).
    Eventual Consistency: Views sind kurzzeitig outdated.
    """
    
    def project_email_categorized(self, event):
        """
        Wenn Email kategorisiert wurde, aktualisiere Views.
        """
        email_id = event['payload']['emailId']
        category = event['payload']['category']
        
        # 1. Inbox View aktualisieren
        view = {
            "emailId": email_id,
            "category": category,
            "priority": self._calculate_priority(category),
            "status": "awaiting_action",
            "categorizedAt": event['timestamp'],
            "searchableText": f"{category} {event['payload'].get('subject', '')}"
        }
        
        write_file(
            path=f"memory/views/inbox/{email_id}.json",
            content=json.dumps(view, indent=2)
        )
        
        # 2. Search Index aktualisieren
        self._update_search_index(email_id, [
            category,
            view['priority'],
            event['payload'].get('sender_domain', '')
        ])
        
        # 3. Category-specific View
        self._add_to_category_view(category, email_id, view)
    
    def _update_search_index(self, email_id, keywords):
        """
        Umgekehrter Index für schnelle Suche.
        """
        for keyword in keywords:
            index_path = f"memory/search-index/{keyword}.json"
            
            try:
                index = json.loads(read_file(index_path))
            except:
                index = {"emails": []}
            
            if email_id not in index["emails"]:
                index["emails"].append(email_id)
                write_file(index_path, json.dumps(index, indent=2))
```

---

### Phase 3: Saga Pattern implementieren

#### 3.1 Saga Definition
```yaml
# sagas/email-processing.yaml
saga:
  name: email-processing-v2
  version: "2.0.0"
  description: "Complete email processing with compensation"
  
  steps:
    - id: 1
      name: extract
      description: "Extract email from IMAP"
      action:
        type: command
        handler: ExtractEmailHandler
        timeout: 30
      compensation:
        type: script
        command: "python3 scripts/mark_unread.py {{emailId}}"
      retry:
        maxAttempts: 3
        backoff: exponential
        
    - id: 2
      name: categorize
      description: "AI categorization"
      action:
        type: agent
        agentId: categorizer-v2
        taskTemplate: "Categorize email {{emailId}}"
        timeout: 60
      compensation:
        type: command
        handler: ResetCategoryHandler
      retry:
        maxAttempts: 2
        
    - id: 3
      name: summarize
      description: "Generate TL;DR summary"
      action:
        type: agent
        agentId: summarizer-v1
        timeout: 45
      # Keine Compensation nötig (keine Seiteneffekte)
      
    - id: 4
      name: route
      description: "Route to appropriate handler"
      action:
        type: router
        rules:
          - condition: "category == 'lead' AND priority >= 8"
            action: notify_sales
          - condition: "category == 'support'"
            action: create_ticket
          - condition: "category == 'spam'"
            action: archive
      compensation:
        type: command
        handler: UnrouteHandler
        
    - id: 5
      name: execute
      description: "Execute final action"
      action:
        type: conditional
        basedOn: route_result
      compensation:
        type: script
        command: "python3 scripts/undo_action.py {{action}} {{emailId}}"
```

#### 3.2 Saga Orchestrator
```python
# sagas/orchestrator.py

class EmailProcessingSaga:
    """
    Orchestriert die Email-Verarbeitung mit Compensation.
    State wird in memory/sagas/ persistiert.
    """
    
    STATES = ['pending', 'running', 'completed', 'compensating', 'compensated', 'failed']
    
    def __init__(self, saga_id, email_id, definition_path):
        self.saga_id = saga_id
        self.email_id = email_id
        self.definition = self._load_definition(definition_path)
        self.state = self._load_or_init_state()
    
    def execute(self):
        """
        Führt die Saga aus oder setzt sie fort.
        """
        steps = self.definition['steps']
        start_from = self.state['currentStep']
        
        for i in range(start_from, len(steps)):
            step = steps[i]
            self._update_state(currentStep=i, status='running_step')
            
            try:
                # Step ausführen
                result = self._execute_step(step)
                
                # State aktualisieren
                self._update_state(
                    currentStep=i + 1,
                    stepResults={**self.state.get('stepResults', {}), step['name']: result}
                )
                
            except Exception as e:
                # Compensation erforderlich
                self._update_state(status='compensating', error=str(e))
                self._compensate(i - 1)
                self._update_state(status='compensated')
                raise SagaFailedException(f"Step {step['name']} failed: {e}")
        
        self._update_state(status='completed')
        return self.state
    
    def _execute_step(self, step):
        """
        Einzelnen Step ausführen.
        """
        print(f"  Executing step: {step['name']}")
        
        action = step['action']
        
        if action['type'] == 'command':
            # Command Handler aufrufen
            handler = self._get_handler(action['handler'])
            command = self._create_command(step)
            return handler.handle(command)
        
        elif action['type'] == 'agent':
            # Sub-Agent spawnen
            return sessions_spawn(
                task=action['taskTemplate'].replace('{{emailId}}', self.email_id),
                agentId=action['agentId'],
                timeoutSeconds=action.get('timeout', 60)
            )
        
        elif action['type'] == 'router':
            # Routing basierend auf aktuellem Context
            return self._execute_routing(action['rules'])
    
    def _compensate(self, last_completed_step):
        """
        Führt Compensation für alle abgeschlossenen Steps aus.
        Rückwärts, beginnend mit dem letzten abgeschlossenen.
        """
        steps = self.definition['steps']
        
        for i in range(last_completed_step, -1, -1):
            step = steps[i]
            
            if 'compensation' not in step:
                continue
            
            try:
                print(f"  Compensating step: {step['name']}")
                
                compensation = step['compensation']
                
                if compensation['type'] == 'script':
                    command = compensation['command'].replace('{{emailId}}', self.email_id)
                    exec(command=command, timeout=30)
                
                elif compensation['type'] == 'command':
                    handler = self._get_handler(compensation['handler'])
                    handler.compensate(self.email_id)
                
                # Compensation loggen
                self._log_compensation(step['name'], 'success')
                
            except Exception as e:
                # Compensation failure loggen
                self._log_compensation(step['name'], 'failed', str(e))
                # Continue with other compensations
    
    def _update_state(self, **updates):
        """
        Persistiert Saga State.
        """
        self.state.update(updates)
        self.state['lastUpdated'] = datetime.utcnow().isoformat()
        
        write_file(
            path=f"memory/sagas/active/{self.saga_id}.json",
            content=json.dumps(self.state, indent=2)
        )
    
    def _load_or_init_state(self):
        """
        Lädt existierenden State oder erstellt neuen.
        """
        try:
            return json.loads(
                read_file(f"memory/sagas/active/{self.saga_id}.json")
            )
        except:
            return {
                'sagaId': self.saga_id,
                'emailId': self.email_id,
                'status': 'pending',
                'currentStep': 0,
                'stepResults': {},
                'compensationLog': [],
                'createdAt': datetime.utcnow().isoformat()
            }
```

#### 3.3 Saga Cron Job (Recovery)
```json
{
  "name": "saga-recovery",
  "schedule": {"kind": "every", "everyMs": 60000},
  "payload": {
    "kind": "agentTurn",
    "message": "Check memory/sagas/active/ for stalled sagas (no update in >5min). For each stalled saga: 1) Load definition from sagas/email-processing.yaml, 2) Resume from current step, 3) If step failed 3x, trigger compensation",
    "model": "kimi-coding/k2p5"
  },
  "sessionTarget": "isolated",
  "delivery": {"mode": "none"}
}
```

---

## Vergleich: Vorher vs Nachher

### Fehlerbehandlung
```python
# VORHER: Keine Compensation
def process_email(email_id):
    extract(email_id)      # ✅
    categorize(email_id)   # ✅
    send_to_hubspot(email_id)  # ❌ FAIL!
    # Email ist als "processed" markiert,
    # aber nicht in HubSpot
    # → Dateninkonsistenz

# NACHHER: Mit Compensation
def process_email(email_id):
    saga = EmailProcessingSaga(email_id)
    try:
        saga.execute()     # ❌ FAIL bei HubSpot!
    except SagaFailedException:
        saga.compensate()  # ↩️ Undo extract, undo categorize
        # Email bleibt unverändert
        # → Konsistent
```

### Parallelisierung
```python
# VORHER: Sequentiell
for email in emails:
    process(email)  # 30s pro Email
# 10 Emails = 300s = 5 Minuten

# NACHHER: Parallel
for email in emails:
    sessions_spawn(
        task=f"Process {email.id}",
        agentId="saga-executor"
    )
# 10 Emails = 30s (parallel)
```

### Observability
```python
# VORHER: Logs nur in einer Datei
log.info("Processing email")

# NACHHER: Jedes Event ist nachvollziehbar
# memory/events/email-received/{id}.json
# memory/events/email-categorized/{id}.json
# memory/sagas/active/{saga_id}.json
# memory/views/inbox/{email_id}.json
```

---

## Migration Checklist

### Woche 1: Vorbereitung
- [ ] Event Schemas definieren
- [ ] Saga Definition schreiben
- [ ] Command Handler implementieren
- [ ] Projection Logic schreiben

### Woche 2: Parallelbetrieb
- [ ] Neues System parallel aufsetzen
- [ ] Events beide Systeme schreiben lassen
- [ ] Queries auf neues System umleiten
- [ ] Monitoring aufsetzen

### Woche 3: Cutover
- [ ] Altes System auf read-only
- [ ] Neues System übernimmt Writes
- [ ] Compensation-Logik testen
- [ ] Performance-Tests

### Woche 4: Cleanup
- [ ] Alte Skripte entfernen
- [ ] Dokumentation aktualisieren
- [ ] Team-Training
- [ ] Post-Mortem

---

## Erwartete Ergebnisse

| Metrik | Vorher | Nachher | Verbesserung |
|--------|--------|---------|--------------|
| Verarbeitung/Email | 30s | 8s | 4x schneller |
| Parallelisierung | 1 | 10+ | 10x Durchsatz |
| Fehlerrate | 5% | 0.1% | 50x besser |
| Recovery-Zeit | 30min | 1min | 30x schneller |
| Test-Coverage | 40% | 85% | 2x besser |
