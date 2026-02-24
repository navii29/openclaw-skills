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

## Letzte Updates

**2026-02-24**: Deep-Dive Session zu Advanced Patterns abgeschlossen. Prototyp läuft. Migration-Guides erstellt.
