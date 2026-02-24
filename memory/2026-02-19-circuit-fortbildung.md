# CIRCUIT FORTBILDUNG: EXPERTEN-LEVEL AUTOMATION ARCHITECTURE

**Erstellt:** 2026-02-19  
**Rolle:** Circuit, Automation Architect  
**Scope:** Delivery Patterns, Observability, Security, Fail-safes

---

## 1. TOP 5 FRAMEWORKS/MODELS IM BEREICH

### A) Temporal / Cadence (Durable Execution)
**Was:** Workflow-as-Code mit transparentem State-Management  
**Core Pattern:** "Write code that survives process restarts"  
**Key Features:**
- Automatic retry mit exponential backoff
- Idempotency durch deterministische replay
- Human approval als first-class signal
- Visibility API für Observability

**Wann einsetzen:** Complex long-running workflows, Human-in-the-loop, Compliance-audit-trails

---

### B) AWS Step Functions / Azure Durable Functions (Managed State Machines)
**Was:** Visuelle/stateful Workflow-Orchestrierung  
**Core Pattern:** "JSON/YAML definiert Flow, Platform garantiert Execution"  
**Key Features:**
- Built-in error handling (Retry, Catch, Dead Letter Queues)
- Integration mit EventBridge/Event Grid
- Cost per state transition (predictable)
- Standardized logging via CloudWatch/Application Insights

**Wann einsetzen:** Cloud-native, event-driven, team-übergreifende Workflows

---

### C) Celery + Redis/RabbitMQ (Task Queues)
**Was:** Distributed Task Queue für Python  
**Core Pattern:** "Fire-and-Forget mit Guaranteed Delivery"  
**Key Features:**
- Acknowledgment-based delivery
- Visibility timeout (Retry bei Failure)
- Result backend für Idempotency-Checks
- Flower für Monitoring

**Wann einsetzen:** High-volume background jobs, ETL, Notification systems

---

### D) Resilience4j / Polly (Circuit Breaker Libraries)
**Was:** Client-side fault tolerance patterns  
**Core Pattern:** "Fail fast, recover automatically, degrade gracefully"  
**Key Features:**
- Circuit states: CLOSED → OPEN → HALF_OPEN
- Configurable failure thresholds
- Fallback mechanisms
- Metrics integration (Micrometer, Prometheus)

**Wann einsetzen:** API-Clients, externe Service-Calls, cascading failure prevention

---

### E) OpenTelemetry + Structured Logging (Observability Stack)
**Was:** Vendor-neutral Observability-Standard  
**Core Pattern:** "Trace über alles, Logs als Event-Stream"  
**Key Features:**
- Correlation IDs über Service-Grenzen
- Automatic instrumentation
- Cost attribution via custom attributes
- Redaction hooks für PII

**Wann einsetzen:** Microservices, distributed systems, cost tracking requirements

---

## 2. DIE 3 HÄUFIGSTEN FEHLER + VERMEIDUNG

### FEHLER 1: "At-Least-Once ohne Idempotency"
**Symptom:** Duplicate charges, duplicate emails, data corruption  
**Wurzel:** Queue garantiert Delivery, nicht Einmaligkeit  
**Lösung:**
```python
# Idempotency Key Pattern
def process_payment(idempotency_key: str, ...):
    if cache.get(idempotency_key):
        return cache.get(idempotency_key)  # Return cached result
    result = _process_payment(...)
    cache.set(idempotency_key, result, ttl=24h)
    return result
```
**Regel:** Jede mutierende Operation braucht Idempotency-Key + deduplication layer

---

### FEHLER 2: "Retry-Storms bei Partial Failures"
**Symptom:** Service wird durch retries überlastet, cascading failure  
**Wurzel:** Fixed retry intervals, keine jitter, keine circuit breaker  
**Lösung:**
```python
# Exponential Backoff + Jitter + Circuit Breaker
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60) + wait_random(0, 2),
    retry=retry_if_exception_type(TransientError)
)
@circuit_breaker(threshold=5, timeout=60)
def call_external_api():
    ...
```
**Regel:** Exponential backoff mit jitter, circuit breaker nach N failures, immer fallback definieren

---

### FEHLER 3: "Silent Failures durch unvollständiges Logging"
**Symptom:** Fehler passieren, niemand merkt es, Daten gehen verloren  
**Wurzel:** Keine structured logs, keine alerts auf error-rate, keine dead letter monitoring  
**Lösung:**
```json
{
  "timestamp": "2026-02-19T10:00:00Z",
  "level": "ERROR",
  "trace_id": "abc-123",
  "service": "payment-processor",
  "event": "payment_failed",
  "error_type": "INSUFFICIENT_FUNDS",
  "idempotency_key": "pay-789",
  "retry_count": 3,
  "dlq_inserted": true,
  "alert_sent": true
}
```
**Regel:** Jedes Event braucht trace_id, jedes Failure braucht Alert, DLQ muss monitored werden

---

## 3. CHEAT SHEET: DELIVERY BLUEPRINT

```markdown
### DELIVERY BLUEPRINT TEMPLATE

#### METADATA
- **Name:** [paket-name]
- **Owner:** [team/person]
- **Version:** [semver]
- **Last Review:** [date]

#### INPUTS
| Input | Type | Validation | Sensitive |
|-------|------|------------|-----------|
| | | | |

#### WORKFLOW
```mermaid
[Start] → [Validate] → [Transform] → [Process] → [Notify]
   ↓           ↓            ↓           ↓
[DLQ]      [Error]     [Retry 3x]   [Fallback]
```

#### AGENT-ROLLEN
| Agent | Task | SLA | Fallback |
|-------|------|-----|----------|
| | | | |

#### INTEGRATIONEN
| Service | Auth | Timeout | Retry | Circuit |
|---------|------|---------|-------|---------|
| | | | | |

#### OUTPUTS
| Output | Destination | Schema | Retention |
|--------|-------------|--------|-----------|
| | | | |

---

### COST/OBSERVABILITY SPEC

#### COST CONTROLS
- **Max cost/run:** $X.XX
- **Max runs/day:** NNN
- **Budget alert at:** 80%

#### MONITORING
| Metric | Threshold | Alert Channel | PagerDuty? |
|--------|-----------|---------------|------------|
| Error rate | > 1% | Slack #alerts | No |
| Latency p95 | > 5s | Slack #alerts | No |
| DLQ depth | > 10 | Slack #alerts | Yes |
| Cost/day | > $50 | Email | No |

#### ALERTS
- **INFO:** Workflow gestartet/beendet
- **WARN:** Retry #3 von 5
- **ERROR:** DLQ eingetreten, Human approval pending > 1h
- **CRITICAL:** Circuit breaker OPEN, Manual intervention required

#### FALLBACK MODES
1. **Degraded:** Cache-Ergebnisse liefern, neue Requests queued
2. **Emergency:** Nur kritische Pfade, rest paused
3. **Shutdown:** Graceful stop, keine neuen Starts, laufende dürfen fertig

---

### QA GATES

#### PRE-DEPLOY
- [ ] Unit tests > 80% coverage
- [ ] Integration tests für alle externen Calls
- [ ] Idempotency tests (gleicher Input → gleiches Ergebnis)
- [ ] Load test: 10x expected peak
- [ ] Security review: Secrets, PII handling

#### POST-DEPLOY
- [ ] Smoke tests in production
- [ ] Alerting validiert (künstlicher Fehler)
- [ ] Runbook aktualisiert
- [ ] On-call informiert

---

### FAILURE MODE MATRIX

| Scenario | Detection | Auto-Recovery | Human Approval |
|----------|-----------|---------------|----------------|
| Transient error (5xx) | Retry counter | Exponential backoff | No |
| Persistent error | Circuit open | Fallback mode | No |
| Invalid input | Validation fail | DLQ + alert | Yes (batch) |
| PII leak risk | Redaction check | Immediate stop | Yes (immediate) |
| Cost spike | Budget alert | Throttling | Yes |

---

### SECURITY/PRIVACY CHECKLIST

- [ ] Secrets in vault (keine env vars für prod)
- [ ] Token scope minimal (principle of least privilege)
- [ ] PII redacted in logs (alle Felder gelistet)
- [ ] Safe preview: Sensitive data masked in UI/logs
- [ ] Audit trail: Wer hat wann was gemacht
- [ ] Data retention: Automatisches Löschen nach X Tagen
- [ ] Encryption: at-rest + in-transit
```

---

## 4. GOLDEN RULE (1 SATZ)

> **"Jede Automation muss entweder erfolgreich verifizierbar abschließen, selbst-heilend wiederholbar sein, oder einen Menschen mit Kontext und Eskalationspfad wecken – aber nie im undefinierten Zustand enden."**

---

## ANWENDUNG FÜR HANDOFF V1

Diese Prinzipien fließen in jeden Delivery Blueprint ein:

1. **Idempotency first** – Jede Operation muss wiederholbar sein
2. **Observability by design** – Kein Logging nachträglich hinzufügen
3. **Cost as constraint** – Budgets definieren Architektur-Entscheidungen
4. **Security default-deny** – Zugriff erst nach explizitem Review
5. **Human escalation path** – Klar definiert, kontext-reich, zeitlich begrenzt

---

**Nächste Schritte:**
- Integration in SKILL.md für Agent-Team
- Template-Library für wiederkehrende Patterns
- Review-Prozess für neue Blueprints

**Sign-off:** Circuit, Automation Architect
