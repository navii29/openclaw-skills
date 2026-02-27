# MEMORY.md - Long-Term Memory

**Meine gelernten Patterns, Entscheidungen und Präferenzen**

---

## Advanced Automation Patterns (Deep-Dive Session: 2026-02-24)

### Was ich gelernt habe

1. **Event-Driven Architecture (EDA)**
   - Cron Jobs als Event Emitter
   - sessions_spawn als Event Consumer
   - Memory als Event Store
   - Lose Kopplung ermöglicht Skalierung

2. **CQRS (Command Query Responsibility Segregation)**
   - Write Model: Commands, Aggregates, Events
   - Read Model: Projections, Views, memory_search
   - Separate Optimierung für Read/Write
   - Eventual Consistency ist akzeptabel

3. **Saga Pattern**
   - Kompensierbare Transaktionen
   - Retry-Logik pro Step
   - State Machine im memory/sagas/
   - Compensation-Chain bei Fehlern

### Wo diese Patterns 10x besser machen

| Skill | Aktuell | Mit Patterns | Impact |
|-------|---------|--------------|--------|
| Inbox AI | Python-Skripte | EDA + Saga | 10x Skalierung |
| Lead Qualification | Synchrone Chain | CQRS + Async | 10x Zuverlässigkeit |
| Document Processing | Single-threaded | Parallel Sagas | 10x Durchsatz |
| Executive Calendar | Direkte API Calls | Event-Driven | 10x Reaktionszeit |

### Entscheidungen

- **Für neue Skills**: Pattern-nativ bauen (EDA + CQRS + Saga)
- **Bestehende Skills**: Migration in Phasen (Events zuerst, dann CQRS, dann Saga)
- **Tool-Wahl**: 
  - Cron für zeitbasierte Events
  - sessions_spawn für parallele Verarbeitung
  - memory_search für alle Queries

### Ressourcen (Workspace)

- `research/advanced-patterns-deep-dive.md` - Theoretische Grundlagen
- `skills/advanced-patterns-prototype.py` - Funktionierender Prototyp
- `research/openclaw-patterns-implementation-guide.md` - Implementierungsdetails
- `research/pattern-migration-inbox-ai.md` - Konkrete Migration
- `research/advanced-patterns-quick-reference.md` - Schnellübersicht

---

## Persönliche Präferenzen

### Code-Stil
- Explizit > Implizit
- Kommentare für komplexe Logik
- Type Hints wo möglich
- Fehlerbehandlung immer definieren

### Architektur
- Lose Kopplung über enge Kopplung
- Events über direkte Calls
- Compensation über Rollback
- Async über Sync (wo möglich)

### Dokumentation
- SKILL.md für jeden Skill
- Event Schemas dokumentieren
- Migration-Guides schreiben
- Lessons Learned aufzeichnen

---

## Wichtige Kontakte & Credentials

Siehe TOOLS.md für:
- Email-Accounts (IONOS, Gmail)
- API Keys (n8n, Telegram, Moltbook)
- Calendly-Zugang

---

## Laufende Projekte

### Aktuell (Februar 2026)
1. **Inbox AI v2** - Migration zu Advanced Patterns
2. **Lead Qualification** - HubSpot ↔ OpenClaw Bridge
3. **OPSMIND** - Knowledge Base für Automation

### Backlog
- Document Processing Pipeline
- Executive Calendar v2
- A2A Market Integration

---

## Zitate & Weisheiten

> "Events sind das API zwischen Services."
> "Compensation > Rollback."
> "Eventual Consistency ist ein Feature, nicht ein Bug."
> "Lieber explizit und langsam als implizit und broken."

---

## Automation Integration (Learning Session 2: 2026-02-26)

### Was ich gelernt habe

1. **Bidirectional Bridge Pattern**
   - Nicht nur n8n → OpenClaw (sessions_spawn)
   - Sondern auch OpenClaw → n8n (webhook commands)
   - Ermöglicht echte "Agent Action" Fähigkeiten
   - Unified API für alle externen Systeme

2. **Command Router Pattern**
   - Ein zentraler n8n Webhook empfängt alle Commands
   - Switch-Node routed zu spezialisierten Sub-Flows
   - Jeder Command = ein klar definierter Vertrag
   - Einfaches Hinzufügen neuer Commands

3. **Skill-First Architecture**
   - Python-Skill als Wrapper für HTTP calls
   - Convenience-Funktionen für häufige Operationen
   - Error Handling und Retry-Logik zentralisiert
   - Type Hints für bessere IDE-Unterstützung

### Integration: Agent Command Center

**Konzept:** OpenClaw kann jetzt aktiv Systeme steuern:
- CRM Updates (HubSpot)
- Slack Notifications
- Email Versand
- Calendar Blocking
- Notion Page Creation

**Implementierung:**
- `skills/n8n_bridge/skill.py` - Python Client
- `n8n-workflows/06-openclaw-command-router.json` - n8n Workflow
- `INTEGRATION-AGENT-COMMAND-CENTER.md` - Dokumentation

### Use Cases für Kunden

| Use Case | Commands | Zeitersparnis |
|----------|----------|---------------|
| Lead-Qualifizierung | crm_create + slack_notify + email_send | 5h/Woche |
| Meeting-Prep | research + notion_create + calendar_block | 3h/Woche |
| Kunden-Support | sentiment + crm_update + escalation | 2h/Woche |

### Pricing
- **Starter:** €1.500 Setup + €200/Monat
- **Professional:** €2.500 Setup + €400/Monat
- **Enterprise:** €5.000 Setup + €800/Monat

---

## Letzte Updates

**2026-02-26**: Learning Session 2 - Bidirectional n8n Bridge implementiert. POC komplett, bereit für Deployment.

**2026-02-24**: Deep-Dive Session zu Advanced Patterns abgeschlossen. Prototyp läuft. Migration-Guides erstellt.
