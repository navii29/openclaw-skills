"""
Patterns Demo
Vollständige Demonstration von EDA, CQRS und Saga Pattern
"""
import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace')

from patterns.core.event_bus import EventBus, Event, emit_domain_event
from patterns.core.cqrs import CQRSStore, Command
from patterns.core.saga import SagaOrchestrator, Saga
from patterns.sagas.email_processing import (
    initialize_orchestrator,
    initialize_event_bus,
    create_email_processing_saga
)
import json


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    print(f"\n▶ {title}")
    print("-" * 50)


# =============================================================================
# DEMO 1: Event-Driven Architecture (EDA)
# =============================================================================

def demo_eda():
    print_header("DEMO 1: Event-Driven Architecture (EDA)")
    print("Kernkonzept: Komponenten kommunizieren durch Events")
    
    bus = initialize_event_bus()
    
    print_section("Publishing Events")
    
    # Event 1: Email received
    event1 = emit_domain_event(
        domain="email",
        action="received",
        aggregate_id="msg-001",
        payload={
            "subject": "Anfrage: Automation für mein Unternehmen",
            "sender": "max.mustermann@beispiel.de",
            "body_preview": "Hallo, ich hätte gerne ein Angebot für..."
        },
        source="inbox-ai"
    )
    bus.publish(event1)
    
    # Event 2: Lead qualified
    event2 = emit_domain_event(
        domain="lead",
        action="qualified",
        aggregate_id="lead-001",
        payload={
            "email": "max.mustermann@beispiel.de",
            "company": "Musterfirma GmbH",
            "score": 85
        },
        source="lead-qualifier"
    )
    bus.publish(event2)
    
    print_section("Query Events")
    events = bus.get_events(event_type="email.received", limit=5)
    print(f"Gefundene Email-Events: {len(events)}")
    for e in events:
        print(f"  - {e.event_type} von {e.source}")
    
    print("\n✅ EDA Demo abgeschlossen")
    print("   Vorteile: Lose Kopplung, Skalierbarkeit, Erweiterbarkeit")


# =============================================================================
# DEMO 2: CQRS (Command Query Responsibility Segregation)
# =============================================================================

def demo_cqrs():
    print_header("DEMO 2: CQRS - Command Query Responsibility Segregation")
    print("Kernkonzept: Trennung von Schreib- und Leseoperationen")
    
    store = CQRSStore()
    
    # Command Handler registrieren
    from patterns.sagas.email_processing import ReceiveEmailHandler, CategorizeEmailHandler
    store.command_bus.register("email.receive", ReceiveEmailHandler())
    store.command_bus.register("email.categorize", CategorizeEmailHandler())
    
    print_section("COMMAND SIDE: Write Operations")
    
    # Command 1: Email empfangen
    cmd1 = Command(
        command_type="email.receive",
        aggregate_id="email-001",
        payload={
            "subject": "Angebot angefordert",
            "sender": "kunde@firma.de",
            "body": "Bitte senden Sie mir ein Angebot..."
        }
    )
    result1 = store.execute_command(cmd1)
    print(f"✉️  Command ausgeführt: email.receive")
    print(f"   Result: {result1}")
    
    # Command 2: Email kategorisieren
    cmd2 = Command(
        command_type="email.categorize",
        aggregate_id="email-001",
        payload={
            "category": "lead",
            "confidence": 0.95
        }
    )
    result2 = store.execute_command(cmd2)
    print(f"\n🏷️  Command ausgeführt: email.categorize")
    print(f"   Result: {result2}")
    
    print_section("QUERY SIDE: Read Operations")
    
    # Read View erstellen
    store.read_model.save_view("inbox-summary", "today", {
        "date": "2026-02-26",
        "totalEmails": 42,
        "highPriority": 5,
        "categories": {
            "lead": 3,
            "support": 8,
            "general": 31
        }
    })
    
    # View abfragen
    view = store.read_model.get_view("inbox-summary", "today")
    print(f"📊 Read View: inbox-summary")
    print(f"   {json.dumps(view, indent=4)}")
    
    print("\n✅ CQRS Demo abgeschlossen")
    print("   Vorteile: Optimierte Read-Performance, separate Skalierung")


# =============================================================================
# DEMO 3: Saga Pattern
# =============================================================================

def demo_saga():
    print_header("DEMO 3: Saga Pattern für Verteilte Transaktionen")
    print("Kernkonzept: Kompensierbare Aktionen für Konsistenz")
    
    orchestrator = initialize_orchestrator()
    
    print_section("Success Case: Email Processing Saga")
    print("5 Schritte: Extract → Categorize → Prioritize → Route → Execute\n")
    
    context = {
        "email_id": "email-123",
        "subject": "Re: Anfrage Automation",
        "sender": "ceo@enterprise.com"
    }
    
    saga_id = orchestrator.start_saga("email-processing", context)
    state = orchestrator.get_saga_status(saga_id)
    
    print(f"\n📋 Saga Status: {state.status.value}")
    print(f"   Saga ID: {saga_id}")
    
    print_section("Failure Case mit Compensation")
    print("Simuliere Fehler in Step 3 und zeige Compensation Chain\n")
    
    # Manuelle Saga mit Fehler
    failing_saga = Saga("email-processing-fail")
    
    def failing_step(ctx):
        print("  ❌ [Failing Step] Fehler aufgetreten!")
        raise Exception("Simulierter Fehler")
    
    def compensate_a(ctx):
        print("  ↩️  [Compensation A] Rollback durchgeführt")
    
    def compensate_b(ctx):
        print("  ↩️  [Compensation B] Rollback durchgeführt")
    
    failing_saga.add_step("step1", lambda ctx: {"ok": True}, compensate_a)
    failing_saga.add_step("step2", lambda ctx: {"ok": True}, compensate_b)
    failing_saga.add_step("step3", failing_step, None)
    
    try:
        failing_saga.execute({"test": "data"})
    except:
        pass
    
    print(f"\n📋 Saga Status: {failing_saga.state.status.value}")
    
    print("\n✅ Saga Demo abgeschlossen")
    print("   Vorteile: Konsistenz, Fehlertoleranz, automatisches Rollback")


# =============================================================================
# DEMO 4: Kombinierte Patterns
# =============================================================================

def demo_combined():
    print_header("DEMO 4: Alle Patterns kombiniert")
    print("Real-world Szenario: Email Automation Pipeline")
    
    bus = initialize_event_bus()
    store = CQRSStore()
    orchestrator = initialize_orchestrator()
    
    print_section("Szenario: Neue Email kommt ein")
    
    # 1. Event emittieren (EDA)
    print("1. Email Received Event wird emittiert...")
    event = emit_domain_event(
        domain="email",
        action="received",
        aggregate_id="email-live-001",
        payload={
            "subject": "Dringend: Angebot für 100 Automatisierungen",
            "sender": "procurement@enterprise.com",
            "body": "Wir benötigen ein Angebot für..."
        }
    )
    bus.publish(event)
    
    # 2. Command ausführen (CQRS)
    print("\n2. Command wird ausgeführt...")
    store.command_bus.register("email.receive", 
        __import__('patterns.sagas.email_processing', fromlist=['ReceiveEmailHandler']).ReceiveEmailHandler())
    
    cmd = Command(
        command_type="email.receive",
        aggregate_id="email-live-001",
        payload={
            "subject": "Dringend: Angebot für 100 Automatisierungen",
            "sender": "procurement@enterprise.com",
            "body": "Wir benötigen ein Angebot für..."
        }
    )
    store.execute_command(cmd)
    
    # 3. Saga starten (Saga)
    print("\n3. Saga wird gestartet...")
    saga_id = orchestrator.start_saga("email-processing", {
        "email_id": "email-live-001",
        "subject": "Dringend: Angebot für 100 Automatisierungen",
        "sender": "procurement@enterprise.com"
    })
    
    state = orchestrator.get_saga_status(saga_id)
    
    print("\n" + "=" * 50)
    print("ERGEBNIS:")
    print("=" * 50)
    print(f"✅ Email verarbeitet")
    print(f"✅ Event gespeichert: {event.event_id}")
    print(f"✅ Command ausgeführt: {cmd.command_id}")
    print(f"✅ Saga abgeschlossen: {saga_id}")
    print(f"   Status: {state.status.value}")
    
    if 'execute_result' in state.context:
        action = state.context['execute_result'].get('action', 'unknown')
        print(f"   Aktion: {action}")
    
    print("\n✅ Kombinierte Demo abgeschlossen")


# =============================================================================
# MAIN
# =============================================================================

def run_all_demos():
    print("\n" + "🚀" * 35)
    print("  OPENCLAW ADVANCED PATTERNS - VOLLSTÄNDIGE DEMO")
    print("🚀" * 35)
    
    demo_eda()
    demo_cqrs()
    demo_saga()
    demo_combined()
    
    print_header("ZUSAMMENFASSUNG")
    print("""
┌─────────────────────────────────────────────────────────────────────┐
│  PATTERN          │  ZWECK                    │  10x IMPACT         │
├─────────────────────────────────────────────────────────────────────┤
│  EDA              │  Lose Kopplung            │  Skalierbarkeit     │
│  CQRS             │  Read/Write Trennung      │  Performance        │
│  Saga             │  Verteilte Transaktionen  │  Zuverlässigkeit    │
└─────────────────────────────────────────────────────────────────────┘

Prototyp implementiert in:
  📁 /Users/fridolin/.openclaw/workspace/patterns/
     ├── core/
     │   ├── event_bus.py      # EDA Implementation
     │   ├── cqrs.py           # CQRS Implementation  
     │   └── saga.py           # Saga Orchestrator
     ├── sagas/
     │   └── email_processing.py  # Beispiel Saga
     └── demo.py               # Diese Demo
""")


if __name__ == "__main__":
    run_all_demos()
