# Advanced Patterns Quick Reference

**Schnellübersicht der 3 Advanced Patterns für OpenClaw**

---

## Pattern 1: Event-Driven Architecture (EDA)

### Wann nutzen?
- Lose Kopplung zwischen Komponenten
- Asynchrone Verarbeitung
- Mehrere Consumer für gleiche Events

### OpenClaw Mapping
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Cron Job   │────▶│   memory/   │────▶│  Handler    │
│  (Emitter)  │     │   events/   │     │  (Consumer) │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                         ┌──────┴──────┐
                                         │sessions_spawn│
                                         └─────────────┘
```

### Code Template
```python
# Emitter (Cron Job)
event = {
    "eventId": str(uuid.uuid4()),
    "eventType": "email.received",
    "timestamp": datetime.utcnow().isoformat(),
    "payload": data,
    "correlationId": saga_id
}
write_file(f"memory/events/{event['eventId']}.json", json.dumps(event))

# Handler
unprocessed = memory_search(query="eventType:email.received status:pending")
for event in unprocessed:
    process_event(event)
    mark_processed(event.id)
```

---

## Pattern 2: CQRS

### Wann nutzen?
- Read/Write unterschiedliche Anforderungen
- Komplexe Queries optimieren
- Audit-Trail benötigt

### OpenClaw Mapping
```
┌──────────────────────────────────────────────────────┐
│                    WRITE SIDE                        │
│  Command ──▶ Handler ──▶ Aggregate ──▶ Event         │
└──────────────────────────────────────────────────────┘
                            │
                            ▼ Project
┌──────────────────────────────────────────────────────┐
│                     READ SIDE                        │
│  Query ──▶ View ──▶ Result                           │
│         (memory_search)                              │
└──────────────────────────────────────────────────────┘
```

### Code Template
```python
# Command (Write)
class CategorizeCommand:
    def __init__(self, email_id, content):
        self.email_id = email_id
        self.content = content

class CategorizeHandler:
    def handle(self, command):
        result = ai_categorize(command.content)
        event = create_event("email.categorized", result)
        update_aggregate(command.email_id, result)
        return event

# Query (Read)
def get_inbox_summary():
    # Nutzt memory_search = schnell
    return memory_search(query="status:unread category:lead")

# Projection (Event → View)
def project(event):
    view = create_view_from_event(event)
    write_file(f"memory/views/{event.email_id}.json", view)
```

---

## Pattern 3: Saga Pattern

### Wann nutzen?
- Verteilte Transaktionen
- Multi-Step Prozesse
- Compensation bei Fehlern

### OpenClaw Mapping
```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Step 1  │───▶│  Step 2  │───▶│  Step 3  │───▶│  Step 4  │
│  Extract │    │ Categorize│   │  Route   │    │ Execute  │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Compensate│    │Compensate│    │Compensate│    │ Complete │
│  (Undo)  │    │  (Undo)  │    │  (Undo)  │    │  Saga    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Code Template
```python
class Saga:
    def __init__(self):
        self.steps = []
        self.state = {}
    
    def add_step(self, action, compensation):
        self.steps.append({
            'action': action,
            'compensation': compensation
        })
    
    def execute(self):
        for i, step in enumerate(self.steps):
            try:
                result = step['action']()
                self.state[f'step_{i}'] = result
            except Exception as e:
                # Compensation
                for j in range(i-1, -1, -1):
                    self.steps[j]['compensation']()
                raise
        return self.state

# Nutzung
saga = Saga()
saga.add_step(extract_email, mark_unread)
saga.add_step(categorize, reset_category)
saga.add_step(route, unroute)
saga.execute()
```

---

## Kombinierte Patterns

### Full Workflow
```
┌─────────────────────────────────────────────────────────────┐
│                         EDA                                  │
│  Cron ──▶ Event ──▶ Handler ──▶ Start Saga                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      SAGA PATTERN                            │
│  Step 1 ──▶ Command ──▶ Event ──▶ Projection ──▶ Next Step   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         CQRS                                 │
│  Write: Command ──▶ Aggregate ──▶ Event Store                │
│  Read:  Query ──▶ memory_search ──▶ Views                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Schnelle Entscheidungen

### Soll ich EDA nutzen?
| Kriterium | Ja | Nein |
|-----------|----|------|
| Mehrere Systeme betroffen? | ✅ | |
| Asynchrone Verarbeitung OK? | ✅ | |
| Echtzeit erforderlich? | | ❌ |
| Komplexe Orchestrierung? | ✅ | |

### Soll ich CQRS nutzen?
| Kriterium | Ja | Nein |
|-----------|----|------|
| Read/Write Ratio > 10:1? | ✅ | |
| Komplexe Queries? | ✅ | |
| Audit-Trail nötig? | ✅ | |
| Einfacher CRUD? | | ❌ |

### Soll ich Saga nutzen?
| Kriterium | Ja | Nein |
|-----------|----|------|
| Multi-Step Prozess? | ✅ | |
| Verteilte Transaktion? | ✅ | |
| Compensation möglich? | ✅ | |
| Einzelner API Call? | | ❌ |

---

## Typische Fehler vermeiden

### EDA Anti-Patterns
- ❌ **Event-Schnittstelle**: Events als API-Ersatz
- ❌ **Meg-Events**: Zu große Payloads
- ❌ **Fehlende Idempotency**: Gleiches Event = verschiedene Ergebnisse
- ✅ **Kleine Events**: Fokussiert, immutable
- ✅ **Event Versioning**: Schema-Änderungen planen

### CQRS Anti-Patterns
- ❌ **Same Model**: Read = Write Model
- ❌ **Sync Projection**: Blockierende Projections
- ❌ **Kein Event Sourcing**: Keine Audit-Trail
- ✅ **Separate Models**: Optimiert für jeweiligen Use Case
- ✅ **Async Projection**: Eventual Consistency akzeptieren

### Saga Anti-Patterns
- ❌ **Fehlende Compensation**: Kein Plan B
- ❌ **Zu lange Sagas**: >10 Steps = problematisch
- ❌ **Keine Timeouts**: Ewig wartende Steps
- ✅ **Compensation pro Step**: Immer definieren
- ✅ **Timeouts**: Max 60s pro Step

---

## OpenClaw Spezifika

### Cron Job Event Emitter
```json
{
  "name": "event-emitter",
  "schedule": {"kind": "every", "everyMs": 300000},
  "payload": {
    "kind": "agentTurn",
    "message": "Emit events...",
    "model": "kimi-coding/k2p5"
  },
  "sessionTarget": "isolated"
}
```

### sessions_spawn als Worker
```python
# Parallelisierung via sessions_spawn
for event in unprocessed_events:
    sessions_spawn(
        task=f"Process {event.id}",
        agentId="event-handler",
        timeoutSeconds=60
    )
```

### memory_search als Query Engine
```python
# Flexible Queries über alle Events
results = memory_search(
    query="eventType:email.categorized priority:HIGH date:today",
    maxResults=100
)
```

---

## Performance Benchmarks

| Pattern | Overhead | Skalierbarkeit | Komplexität |
|---------|----------|----------------|-------------|
| EDA | +10% Latenz | Horizontal | Mittel |
| CQRS | +5% Write | Read-Heavy | Hoch |
| Saga | +20% Latenz | Sequential | Hoch |
| Kombiniert | +30% Latenz | Beides | Sehr Hoch |

---

## Checkliste: Pattern einführen

### Vorbereitung
- [ ] Event Schemas definieren
- [ ] Command/Query Separation planen
- [ ] Saga Steps definieren
- [ ] Compensation für jeden Step

### Implementation
- [ ] Event Bus (Cron + memory/events/)
- [ ] Command Handler
- [ ] Read Model Projections
- [ ] Saga Orchestrator

### Testing
- [ ] Happy Path
- [ ] Compensation Path
- [ ] Retry Logic
- [ ] Concurrent Sagas

### Monitoring
- [ ] Event Lag
- [ ] Saga Duration
- [ ] Compensation Rate
- [ ] Error Rate
