#!/usr/bin/env python3
"""
Advanced Automation Patterns - Prototyp Implementierung
=========================================================

Demonstriert Event-Driven Architecture, CQRS und Saga Pattern
für OpenClaw Skills am Beispiel einer Email-Verarbeitung-Pipeline.

Patterns:
- EDA: Events verbinden Komponenten lose
- CQRS: Separate Read/Write Pfade
- Saga: Kompensierbare Transaktionen

Author: Deep-Dive Session 2026-02-24
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from abc import ABC, abstractmethod


# ============================================================================
# EVENT-DRIVEN ARCHITECTURE (EDA) - Core Components
# ============================================================================

class EventType(Enum):
    """Standardisierte Event-Typen für Email-Verarbeitung"""
    EMAIL_RECEIVED = "email.received"
    EMAIL_EXTRACTED = "email.extracted"
    EMAIL_CATEGORIZED = "email.categorized"
    EMAIL_SUMMARIZED = "email.summarized"
    EMAIL_ROUTED = "email.routed"
    EMAIL_PROCESSED = "email.processed"
    EMAIL_FAILED = "email.failed"
    SAGA_STARTED = "saga.started"
    SAGA_COMPLETED = "saga.completed"
    SAGA_COMPENSATED = "saga.compensated"


@dataclass
class Event:
    """
    Domain Event - das Herzstück der EDA.
    Immutable, zeitlich geordnet, selbstbeschreibend.
    """
    event_id: str
    event_type: EventType
    timestamp: str
    source: str
    payload: Dict[str, Any]
    correlation_id: str
    causation_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        event_type: EventType,
        source: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None
    ) -> "Event":
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            source=source,
            payload=payload,
            correlation_id=correlation_id or str(uuid.uuid4()),
            causation_id=causation_id
        )
    
    def to_dict(self) -> Dict:
        return {
            "eventId": self.event_id,
            "eventType": self.event_type.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "payload": self.payload,
            "correlationId": self.correlation_id,
            "causationId": self.causation_id
        }


class EventBus:
    """
    Event Bus - Zentrale Publish/Subscribe Infrastruktur.
    
    In OpenClaw: Gateway + Cron Jobs + Sessions bilden den Event Bus
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._event_store: List[Event] = []
    
    def subscribe(
        self, 
        event_type: EventType, 
        handler: Callable[[Event], None]
    ) -> None:
        """Handler für Event-Typ registrieren"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        print(f"📡 Subscribed {handler.__name__} to {event_type.value}")
    
    def publish(self, event: Event) -> None:
        """Event veröffentlichen und an alle Handler verteilen"""
        self._event_store.append(event)
        handlers = self._subscribers.get(event.event_type, [])
        
        print(f"\n📤 EVENT PUBLISHED: {event.event_type.value}")
        print(f"   Source: {event.source} | Correlation: {event.correlation_id[:8]}")
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"   ❌ Handler failed: {e}")
    
    def get_events(self, correlation_id: str) -> List[Event]:
        """Alle Events für eine Correlation ID (Saga Tracking)"""
        return [e for e in self._event_store if e.correlation_id == correlation_id]


# ============================================================================
# CQRS - Command Query Responsibility Segregation
# ============================================================================

class Command(ABC):
    """Base Command - immutable instruction to change state"""
    def __init__(self):
        self.command_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()


class ExtractEmailCommand(Command):
    """Command: Email aus IMAP extrahieren"""
    def __init__(self, email_id: str, imap_config: Dict):
        super().__init__()
        self.email_id = email_id
        self.imap_config = imap_config


class CategorizeCommand(Command):
    """Command: Email kategorisieren"""
    def __init__(self, email_data: Dict, category_rules: List[str]):
        super().__init__()
        self.email_data = email_data
        self.category_rules = category_rules


class UpdateReadModelCommand(Command):
    """Command: Read Model aktualisieren (CQRS)"""
    def __init__(self, aggregate_id: str, view_data: Dict):
        super().__init__()
        self.aggregate_id = aggregate_id
        self.view_data = view_data


class CommandHandler(ABC):
    """Abstract Command Handler"""
    @abstractmethod
    def handle(self, command: Command) -> Dict:
        pass


class WriteModel:
    """
    Write Model - Source of Truth für Commands.
    In OpenClaw: Memory Files, Session State, Cron Configs
    """
    
    def __init__(self):
        self._aggregates: Dict[str, Dict] = {}
        self._commands: List[Command] = []
    
    def save(self, aggregate_id: str, data: Dict) -> None:
        """Aggregate speichern"""
        self._aggregates[aggregate_id] = {
            **data,
            "version": self._aggregates.get(aggregate_id, {}).get("version", 0) + 1,
            "lastModified": datetime.utcnow().isoformat()
        }
    
    def get(self, aggregate_id: str) -> Optional[Dict]:
        """Aggregate laden"""
        return self._aggregates.get(aggregate_id)
    
    def log_command(self, command: Command) -> None:
        """Command für Audit-Trail loggen"""
        self._commands.append(command)


class ReadModel:
    """
    Read Model - Optimiert für Queries, eventual consistent.
    In OpenClaw: memory_search, sessions_list, Aggregierte Views
    """
    
    def __init__(self):
        self._views: Dict[str, Dict] = {}
        self._search_index: Dict[str, List[str]] = {}
    
    def project(self, view_id: str, data: Dict) -> None:
        """
        Read Model aus Event projizieren.
        Separate Projection für jede View.
        """
        self._views[view_id] = {
            **data,
            "projectedAt": datetime.utcnow().isoformat()
        }
        
        # Search Index aktualisieren
        for keyword in data.get("keywords", []):
            if keyword not in self._search_index:
                self._search_index[keyword] = []
            if view_id not in self._search_index[keyword]:
                self._search_index[keyword].append(view_id)
    
    def query_by_id(self, view_id: str) -> Optional[Dict]:
        """Direkte Abfrage nach ID"""
        return self._views.get(view_id)
    
    def query_by_keyword(self, keyword: str) -> List[Dict]:
        """Suche über Index"""
        view_ids = self._search_index.get(keyword, [])
        return [self._views[vid] for vid in view_ids if vid in self._views]
    
    def get_stats(self) -> Dict:
        """Query-Statistiken"""
        return {
            "totalViews": len(self._views),
            "indexSize": len(self._search_index),
            "lastUpdated": datetime.utcnow().isoformat()
        }


class CQRSStore:
    """Kombinierter CQRS Store mit Write und Read Model"""
    
    def __init__(self):
        self.write_model = WriteModel()
        self.read_model = ReadModel()
    
    def execute_command(self, command: Command, handler: CommandHandler) -> Event:
        """
        Command ausführen und Event generieren.
        Write Side: Command → Aggregate → Event
        """
        result = handler.handle(command)
        
        # Write Model aktualisieren
        self.write_model.log_command(command)
        
        # Event erstellen
        event = Event.create(
            event_type=result["event_type"],
            source=result["source"],
            payload=result["payload"],
            correlation_id=result.get("correlation_id")
        )
        
        return event
    
    def project_to_read_model(self, event: Event) -> None:
        """
        Read Model aus Event projizieren.
        Read Side: Event → Projection → View
        """
        # Verschiedene Projektionen je nach Event-Typ
        if event.event_type == EventType.EMAIL_CATEGORIZED:
            view_id = event.payload.get("email_id")
            self.read_model.project(view_id, {
                "emailId": view_id,
                "category": event.payload.get("category"),
                "priority": event.payload.get("priority"),
                "keywords": [
                    event.payload.get("category"),
                    event.payload.get("sender_domain"),
                    str(event.payload.get("priority"))
                ],
                "processedAt": event.timestamp
            })


# ============================================================================
# SAGA PATTERN - Distributed Transaction Coordinator
# ============================================================================

class SagaStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


@dataclass
class SagaStep:
    """
    Einzelner Schritt in einer Saga.
    Action = Vorwärts-Aktion
    Compensation = Rückwärts-Aktion bei Fehler
    """
    name: str
    action: Callable[[Dict], Dict]
    compensation: Optional[Callable[[Dict], None]] = None
    max_retries: int = 3


class Saga:
    """
    Saga - Koordiniert verteilte Transaktionen.
    
    Choreography: Events triggern nächsten Schritt
    Orchestration: Dieser Saga-Manager koordiniert
    """
    
    def __init__(self, saga_id: str, name: str, event_bus: EventBus):
        self.saga_id = saga_id
        self.name = name
        self.event_bus = event_bus
        self.steps: List[SagaStep] = []
        self.current_step = 0
        self.status = SagaStatus.PENDING
        self.context: Dict[str, Any] = {}
        self.history: List[Dict] = []
        self.compensation_log: List[Dict] = []
    
    def add_step(self, step: SagaStep) -> "Saga":
        """Schritt zur Saga hinzufügen"""
        self.steps.append(step)
        return self
    
    def execute(self, initial_context: Dict) -> Dict:
        """
        Saga ausführen mit Compensation bei Fehlern.
        
        Pattern: Execute → Success? → Next Step
                           └── No ──▶ Compensate
        """
        self.context = initial_context
        self.context["saga_id"] = self.saga_id
        self.status = SagaStatus.RUNNING
        
        print(f"\n🎬 SAGA STARTED: {self.name}")
        print(f"   Saga ID: {self.saga_id[:8]}")
        print(f"   Steps: {len(self.steps)}")
        
        # Saga Started Event
        self.event_bus.publish(Event.create(
            event_type=EventType.SAGA_STARTED,
            source="saga_orchestrator",
            payload={"sagaId": self.saga_id, "name": self.name},
            correlation_id=self.saga_id
        ))
        
        for i, step in enumerate(self.steps):
            self.current_step = i
            print(f"\n   ▶️  Step {i+1}/{len(self.steps)}: {step.name}")
            
            retry_count = 0
            success = False
            
            while retry_count < step.max_retries and not success:
                try:
                    result = step.action(self.context)
                    self.context.update(result)
                    self.history.append({
                        "step": step.name,
                        "status": "success",
                        "result": result
                    })
                    print(f"      ✅ Success")
                    success = True
                    
                except Exception as e:
                    retry_count += 1
                    print(f"      ⚠️  Attempt {retry_count}/{step.max_retries} failed: {e}")
                    
                    if retry_count >= step.max_retries:
                        print(f"      ❌ Step failed after {step.max_retries} retries")
                        self._compensate(i)
                        return {"status": "failed", "failed_step": step.name, "error": str(e)}
            
            # Publish step completed event
            self.event_bus.publish(Event.create(
                event_type=EventType.EMAIL_PROCESSED if "email" in step.name else EventType.SAGA_COMPLETED,
                source="saga_orchestrator",
                payload={
                    "sagaId": self.saga_id,
                    "step": step.name,
                    "stepNumber": i + 1
                },
                correlation_id=self.saga_id
            ))
        
        self.status = SagaStatus.COMPLETED
        print(f"\n🏁 SAGA COMPLETED: {self.name}")
        
        # Saga Completed Event
        self.event_bus.publish(Event.create(
            event_type=EventType.SAGA_COMPLETED,
            source="saga_orchestrator",
            payload={
                "sagaId": self.saga_id,
                "name": self.name,
                "stepsCompleted": len(self.steps)
            },
            correlation_id=self.saga_id
        ))
        
        return {"status": "completed", "context": self.context}
    
    def _compensate(self, failed_step_index: int) -> None:
        """
        Compensation - Rückwärts-Ausführung bei Fehlern.
        
        Pattern: Fehler in Schritt N → Kompensiere Schritt N-1, N-2, ...
        """
        self.status = SagaStatus.COMPENSATING
        print(f"\n⏮️  COMPENSATION STARTED")
        
        # Rückwärts durchlaufen
        for i in range(failed_step_index - 1, -1, -1):
            step = self.steps[i]
            if step.compensation:
                try:
                    print(f"   ↩️  Compensating: {step.name}")
                    step.compensation(self.context)
                    self.compensation_log.append({"step": step.name, "status": "compensated"})
                except Exception as e:
                    print(f"   ⚠️  Compensation failed for {step.name}: {e}")
                    self.compensation_log.append({"step": step.name, "status": "failed", "error": str(e)})
        
        self.status = SagaStatus.COMPENSATED
        
        # Saga Compensated Event
        self.event_bus.publish(Event.create(
            event_type=EventType.SAGA_COMPENSATED,
            source="saga_orchestrator",
            payload={
                "sagaId": self.saga_id,
                "failedStep": self.steps[failed_step_index].name,
                "compensationLog": self.compensation_log
            },
            correlation_id=self.saga_id
        ))


# ============================================================================
# CONCRETE IMPLEMENTATION - Email Processing mit allen Patterns
# ============================================================================

class EmailProcessingCommandHandler(CommandHandler):
    """Command Handler für Email-Verarbeitung"""
    
    def handle(self, command: Command) -> Dict:
        if isinstance(command, ExtractEmailCommand):
            return self._handle_extract(command)
        elif isinstance(command, CategorizeCommand):
            return self._handle_categorize(command)
        return {}
    
    def _handle_extract(self, cmd: ExtractEmailCommand) -> Dict:
        # Simulierte Email-Extraktion
        return {
            "event_type": EventType.EMAIL_EXTRACTED,
            "source": "inbox_extractor",
            "payload": {
                "email_id": cmd.email_id,
                "subject": "RE: Angebot Automation",
                "sender": "kunde@beispiel.de",
                "body": "Hallo, ich hätte gerne ein Angebot für...",
                "received_at": datetime.utcnow().isoformat()
            },
            "correlation_id": str(uuid.uuid4())
        }
    
    def _handle_categorize(self, cmd: CategorizeCommand) -> Dict:
        # Simulierte Kategorisierung
        return {
            "event_type": EventType.EMAIL_CATEGORIZED,
            "source": "ai_categorizer",
            "payload": {
                "email_id": cmd.email_data.get("email_id"),
                "category": "lead",
                "priority": 8,
                "sender_domain": "beispiel.de",
                "confidence": 0.92
            }
        }


class EmailProcessingSagaBuilder:
    """Baut die Email-Verarbeitung Saga mit allen Schritten"""
    
    @staticmethod
    def build(event_bus: EventBus, cqrs_store: CQRSStore) -> Saga:
        """
        Komplette Email-Verarbeitung Saga:
        
        1. Extract (IMAP)
        2. Categorize (AI)
        3. Summarize (AI)
        4. Route (Decision)
        5. Execute Action (Reply/Forward/Archive)
        """
        
        saga_id = str(uuid.uuid4())
        saga = Saga(saga_id, "email-processing-v1", event_bus)
        
        handler = EmailProcessingCommandHandler()
        
        # Step 1: Extract
        saga.add_step(SagaStep(
            name="extract_email",
            action=lambda ctx: EmailProcessingSagaBuilder._step_extract(ctx, cqrs_store, handler),
            compensation=lambda ctx: EmailProcessingSagaBuilder._compensate_extract(ctx),
            max_retries=3
        ))
        
        # Step 2: Categorize
        saga.add_step(SagaStep(
            name="categorize_email",
            action=lambda ctx: EmailProcessingSagaBuilder._step_categorize(ctx, cqrs_store, handler),
            compensation=lambda ctx: EmailProcessingSagaBuilder._compensate_categorize(ctx),
            max_retries=2
        ))
        
        # Step 3: Summarize
        saga.add_step(SagaStep(
            name="summarize_email",
            action=lambda ctx: EmailProcessingSagaBuilder._step_summarize(ctx),
            compensation=None,  # Summarization hat keine Seiteneffekte
            max_retries=2
        ))
        
        # Step 4: Route
        saga.add_step(SagaStep(
            name="route_email",
            action=lambda ctx: EmailProcessingSagaBuilder._step_route(ctx, event_bus),
            compensation=lambda ctx: EmailProcessingSagaBuilder._compensate_route(ctx),
            max_retries=1
        ))
        
        # Step 5: Execute
        saga.add_step(SagaStep(
            name="execute_action",
            action=lambda ctx: EmailProcessingSagaBuilder._step_execute(ctx),
            compensation=lambda ctx: EmailProcessingSagaBuilder._compensate_execute(ctx),
            max_retries=1
        ))
        
        return saga
    
    @staticmethod
    def _step_extract(ctx: Dict, store: CQRSStore, handler: CommandHandler) -> Dict:
        """Step 1: Email aus IMAP extrahieren"""
        cmd = ExtractEmailCommand(
            email_id=ctx.get("email_id", str(uuid.uuid4())),
            imap_config={"server": "imap.gmail.com", "port": 993}
        )
        event = store.execute_command(cmd, handler)
        store.project_to_read_model(event)
        
        # Event publishen
        event.event_bus = None  # Remove circular ref for serialization
        return {"extract_event": event.to_dict(), "email_data": event.payload}
    
    @staticmethod
    def _compensate_extract(ctx: Dict) -> None:
        """Compensation: Markiere als ungelesen"""
        print(f"      🔄 Marking email {ctx.get('email_id')} as unread")
    
    @staticmethod
    def _step_categorize(ctx: Dict, store: CQRSStore, handler: CommandHandler) -> Dict:
        """Step 2: Email mit AI kategorisieren"""
        email_data = ctx.get("email_data", {})
        cmd = CategorizeCommand(
            email_data=email_data,
            category_rules=["lead", "support", "spam", "newsletter"]
        )
        event = store.execute_command(cmd, handler)
        store.project_to_read_model(event)
        
        return {
            "category": event.payload.get("category"),
            "priority": event.payload.get("priority"),
            "categorization_event": event.to_dict()
        }
    
    @staticmethod
    def _compensate_categorize(ctx: Dict) -> None:
        """Compensation: Reset Kategorie"""
        print(f"      🔄 Resetting category for email")
    
    @staticmethod
    def _step_summarize(ctx: Dict) -> Dict:
        """Step 3: TL;DR Summary generieren"""
        email_data = ctx.get("email_data", {})
        
        # Simulierte AI-Summary
        summary = {
            "tldr": "Kunde möchte Angebot für Automation",
            "key_points": ["Budget offen", "Zeithorizont Q2", "Entscheider erreichbar"],
            "sentiment": "positive",
            "action_required": True
        }
        
        return {"summary": summary, "processing_time_ms": 450}
    
    @staticmethod
    def _step_route(ctx: Dict, event_bus: EventBus) -> Dict:
        """Step 4: Routing basierend auf Kategorie"""
        category = ctx.get("category", "unknown")
        priority = ctx.get("priority", 5)
        
        routing_decisions = {
            "lead": {"action": "notify_sales", "urgency": "high" if priority > 7 else "normal"},
            "support": {"action": "create_ticket", "urgency": "normal"},
            "spam": {"action": "archive", "urgency": "low"},
            "newsletter": {"action": "digest", "urgency": "low"}
        }
        
        decision = routing_decisions.get(category, {"action": "manual_review", "urgency": "normal"})
        
        # Routing Event
        event_bus.publish(Event.create(
            event_type=EventType.EMAIL_ROUTED,
            source="router",
            payload={
                "category": category,
                "decision": decision,
                "email_id": ctx.get("email_data", {}).get("email_id")
            },
            correlation_id=ctx.get("saga_id")
        ))
        
        return {"routing": decision}
    
    @staticmethod
    def _compensate_route(ctx: Dict) -> None:
        """Compensation: Undispatch"""
        print(f"      🔄 Removing from queue")
    
    @staticmethod
    def _step_execute(ctx: Dict) -> Dict:
        """Step 5: Aktion ausführen"""
        routing = ctx.get("routing", {})
        action = routing.get("action", "manual_review")
        
        execution_results = {
            "action": action,
            "executed_at": datetime.utcnow().isoformat(),
            "success": True
        }
        
        print(f"      ✅ Executed action: {action}")
        return {"execution": execution_results}
    
    @staticmethod
    def _compensate_execute(ctx: Dict) -> None:
        """Compensation: Undo Aktion"""
        action = ctx.get("routing", {}).get("action")
        print(f"      🔄 Undoing action: {action}")


# ============================================================================
# EVENT HANDLERS - Reaktion auf Events
# ============================================================================

class NotificationHandler:
    """Handler für Benachrichtigungen basierend auf Events"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._subscribe()
    
    def _subscribe(self) -> None:
        self.event_bus.subscribe(EventType.EMAIL_ROUTED, self.on_email_routed)
        self.event_bus.subscribe(EventType.SAGA_COMPLETED, self.on_saga_completed)
        self.event_bus.subscribe(EventType.SAGA_COMPENSATED, self.on_saga_failed)
    
    def on_email_routed(self, event: Event) -> None:
        """Reagiere auf Email Routing"""
        decision = event.payload.get("decision", {})
        if decision.get("urgency") == "high":
            print(f"   🔔 HIGH PRIORITY: Sending Telegram notification")
            # In echter Implementierung: message.send()
    
    def on_saga_completed(self, event: Event) -> None:
        """Reagiere auf Saga Completion"""
        print(f"   ✅ Saga completed - updating analytics")
    
    def on_saga_failed(self, event: Event) -> None:
        """Reagiere auf Saga Failure"""
        print(f"   ⚠️  Saga failed - alerting admin")


class AnalyticsHandler:
    """Handler für Analytics und Monitoring"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.stats = {
            "emailsProcessed": 0,
            "sagasCompleted": 0,
            "sagasFailed": 0,
            "compensations": 0
        }
        self._subscribe()
    
    def _subscribe(self) -> None:
        self.event_bus.subscribe(EventType.EMAIL_PROCESSED, self.on_email_processed)
        self.event_bus.subscribe(EventType.SAGA_COMPLETED, self.on_saga_completed)
        self.event_bus.subscribe(EventType.SAGA_COMPENSATED, self.on_compensated)
    
    def on_email_processed(self, event: Event) -> None:
        self.stats["emailsProcessed"] += 1
    
    def on_saga_completed(self, event: Event) -> None:
        self.stats["sagasCompleted"] += 1
    
    def on_compensated(self, event: Event) -> None:
        self.stats["compensations"] += 1
        self.stats["sagasFailed"] += 1
    
    def report(self) -> Dict:
        return self.stats


# ============================================================================
# DEMO / PROTOTYP AUSFÜHRUNG
# ============================================================================

def run_demo():
    """
    Vollständige Demo aller Patterns:
    - EDA: Event-getriebene Kommunikation
    - CQRS: Separate Read/Write Modelle
    - Saga: Kompensierbare Transaktionen
    """
    
    print("=" * 70)
    print("ADVANCED AUTOMATION PATTERNS - PROTOTYPE DEMO")
    print("=" * 70)
    print("\n🎯 Patterns: EDA + CQRS + Saga")
    print("📧 Use Case: Email Processing Pipeline")
    print("\n" + "-" * 70)
    
    # Initialisierung
    event_bus = EventBus()
    cqrs_store = CQRSStore()
    
    # Event Handler registrieren
    notification_handler = NotificationHandler(event_bus)
    analytics_handler = AnalyticsHandler(event_bus)
    
    # Saga bauen
    saga = EmailProcessingSagaBuilder.build(event_bus, cqrs_store)
    
    # Saga ausführen
    result = saga.execute({
        "email_id": "demo-email-001",
        "source": "imap://gmail.com"
    })
    
    # Ergebnisse
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\nSaga Status: {result.get('status')}")
    print(f"\nContext:")
    context = result.get('context', {})
    print(f"  - Category: {context.get('category')}")
    print(f"  - Priority: {context.get('priority')}")
    print(f"  - Summary: {context.get('summary', {}).get('tldr')}")
    print(f"  - Routing: {context.get('routing', {}).get('action')}")
    
    print(f"\nAnalytics:")
    print(f"  {analytics_handler.report()}")
    
    print(f"\nRead Model Stats:")
    print(f"  {cqrs_store.read_model.get_stats()}")
    
    print(f"\nEvent Store:")
    events = event_bus.get_events(context.get("saga_id", ""))
    print(f"  Total Events: {len(events)}")
    for e in events:
        print(f"    - {e.event_type.value}")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETED")
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    run_demo()
