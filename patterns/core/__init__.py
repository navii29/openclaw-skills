"""
Advanced Automation Patterns - Core Framework
=============================================

Enterprise-grade patterns for OpenClaw Skills:
- Event-Driven Architecture (EDA)
- CQRS (Command Query Responsibility Segregation)
- Saga Pattern (Distributed Transactions)

Author: Deep-Dive Session 2026-02-25
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Union
import uuid
import json


# ============================================================================
# EVENT-DRIVEN ARCHITECTURE (EDA) - Core Components
# ============================================================================

class EventType(Enum):
    """Standardisierte Event-Typen für Automation"""
    # Email Events
    EMAIL_RECEIVED = "email.received"
    EMAIL_EXTRACTED = "email.extracted"
    EMAIL_CATEGORIZED = "email.categorized"
    EMAIL_SUMMARIZED = "email.summarized"
    EMAIL_ROUTED = "email.routed"
    EMAIL_PROCESSED = "email.processed"
    EMAIL_FAILED = "email.failed"
    
    # Lead Events
    LEAD_CREATED = "lead.created"
    LEAD_QUALIFIED = "lead.qualified"
    LEAD_SCORED = "lead.scored"
    LEAD_ROUTED = "lead.routed"
    
    # Document Events
    DOCUMENT_RECEIVED = "document.received"
    DOCUMENT_EXTRACTED = "document.extracted"
    DOCUMENT_CLASSIFIED = "document.classified"
    
    # Saga Events
    SAGA_STARTED = "saga.started"
    SAGA_STEP_STARTED = "saga.step.started"
    SAGA_STEP_COMPLETED = "saga.step.completed"
    SAGA_STEP_FAILED = "saga.step.failed"
    SAGA_COMPLETED = "saga.completed"
    SAGA_COMPENSATING = "saga.compensating"
    SAGA_COMPENSATED = "saga.compensated"
    
    # System Events
    SYSTEM_HEALTH_CHECK = "system.health_check"
    SYSTEM_ERROR = "system.error"


@dataclass(frozen=True)
class Event:
    """
    Domain Event - das Herzstück der EDA.
    
    Immutable, zeitlich geordnet, selbstbeschreibend.
    Ermöglicht Event Sourcing und Audit-Trail.
    """
    event_id: str
    event_type: EventType
    timestamp: str
    source: str
    payload: Dict[str, Any]
    correlation_id: str
    causation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        event_type: EventType,
        source: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Event":
        """Factory-Methode für Event-Erstellung"""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=source,
            payload=payload,
            correlation_id=correlation_id or str(uuid.uuid4()),
            causation_id=causation_id,
            metadata=metadata or {}
        )
    
    def to_dict(self) -> Dict:
        """Serialisierung für Storage/Transport"""
        return {
            "eventId": self.event_id,
            "eventType": self.event_type.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "payload": self.payload,
            "correlationId": self.correlation_id,
            "causationId": self.causation_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Event":
        """Deserialisierung aus Storage"""
        return cls(
            event_id=data["eventId"],
            event_type=EventType(data["eventType"]),
            timestamp=data["timestamp"],
            source=data["source"],
            payload=data["payload"],
            correlation_id=data["correlationId"],
            causation_id=data.get("causationId"),
            metadata=data.get("metadata", {})
        )
    
    def with_causation(self, previous_event: "Event") -> "Event":
        """Erstellt neues Event mit Causation-Link"""
        return Event.create(
            event_type=self.event_type,
            source=self.source,
            payload=self.payload,
            correlation_id=self.correlation_id,
            causation_id=previous_event.event_id,
            metadata=self.metadata
        )


EventHandler = Callable[[Event], None]


class EventBus:
    """
    Event Bus - Zentrale Publish/Subscribe Infrastruktur.
    
    In OpenClaw: Gateway + Cron Jobs + Sessions bilden den Event Bus
    - Cron Jobs = Event Emitter (zeitbasiert)
    - sessions_spawn = Event Consumer (Verarbeitung)
    - Event Store = Memory Files (memory/YYYY-MM-DD.md)
    """
    
    def __init__(self, persistence_path: Optional[str] = None):
        self._subscribers: Dict[EventType, List[EventHandler]] = {}
        self._event_store: List[Event] = []
        self._persistence_path = persistence_path
        self._stats = {
            "published": 0,
            "handled": 0,
            "errors": 0
        }
    
    def subscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> None:
        """Handler für Event-Typ registrieren"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> bool:
        """Handler deregistrieren"""
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                return True
        return False
    
    def publish(self, event: Event) -> Dict[str, Any]:
        """
        Event veröffentlichen und an alle Handler verteilen.
        
        Returns:
            Dict mit Handler-Ergebnissen
        """
        self._event_store.append(event)
        self._stats["published"] += 1
        
        handlers = self._subscribers.get(event.event_type, [])
        results = {"success": [], "failed": []}
        
        for handler in handlers:
            try:
                handler(event)
                results["success"].append(handler.__name__)
                self._stats["handled"] += 1
            except Exception as e:
                results["failed"].append({
                    "handler": handler.__name__,
                    "error": str(e)
                })
                self._stats["errors"] += 1
        
        return results
    
    def get_events(
        self, 
        correlation_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Events filtern und zurückgeben.
        
        Use Cases:
        - Saga Tracking (via correlation_id)
        - Audit-Trail (via source)
        - Debugging (via event_type)
        """
        events = self._event_store
        
        if correlation_id:
            events = [e for e in events if e.correlation_id == correlation_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if source:
            events = [e for e in events if e.source == source]
        
        return events[-limit:]
    
    def get_event_chain(self, correlation_id: str) -> List[Event]:
        """
        Alle Events einer Saga chronologisch sortiert.
        
        Ermöglicht vollständiges Debugging von Workflows.
        """
        events = self.get_events(correlation_id=correlation_id)
        return sorted(events, key=lambda e: e.timestamp)
    
    def get_stats(self) -> Dict[str, Any]:
        """Event Bus Statistiken"""
        return {
            **self._stats,
            "stored_events": len(self._event_store),
            "active_subscriptions": sum(len(h) for h in self._subscribers.values())
        }
    
    def persist(self, path: Optional[str] = None) -> None:
        """Event Store persistieren"""
        path = path or self._persistence_path
        if path:
            with open(path, 'w') as f:
                events_data = [e.to_dict() for e in self._event_store]
                json.dump(events_data, f, indent=2)
    
    def load(self, path: Optional[str] = None) -> None:
        """Event Store laden"""
        path = path or self._persistence_path
        if path:
            try:
                with open(path, 'r') as f:
                    events_data = json.load(f)
                    self._event_store = [Event.from_dict(e) for e in events_data]
            except FileNotFoundError:
                pass


# ============================================================================
# CQRS - Command Query Responsibility Segregation
# ============================================================================

@dataclass
class Command:
    """Base Command - immutable instruction to change state"""
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    aggregate_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "commandId": self.command_id,
            "commandType": self.__class__.__name__,
            "timestamp": self.timestamp,
            "aggregateId": self.aggregate_id,
            "payload": self.payload,
            "metadata": self.metadata
        }


class CommandHandler(ABC):
    """Abstract Command Handler - CQRS Command Side"""
    
    @abstractmethod
    def handle(self, command: Command) -> Event:
        """
        Command ausführen und Domain Event zurückgeben.
        
        Pattern: Command → Business Logic → Event
        """
        pass
    
    @abstractmethod
    def validate(self, command: Command) -> bool:
        """Command validieren vor Ausführung"""
        pass


class WriteModel:
    """
    Write Model - Source of Truth für Commands.
    
    In OpenClaw:
    - Aggregates in memory/aggregates/
    - Command Log in memory/commands/
    - Event Store via EventBus
    
    Eigenschaften:
    - Strikte Konsistenz
    - Validierung
    - Audit-Trail
    """
    
    def __init__(self):
        self._aggregates: Dict[str, Dict] = {}
        self._command_log: List[Command] = []
    
    def save_aggregate(self, aggregate_id: str, data: Dict) -> None:
        """Aggregate speichern mit Versionierung"""
        current = self._aggregates.get(aggregate_id, {})
        version = current.get("_version", 0) + 1
        
        self._aggregates[aggregate_id] = {
            **data,
            "_version": version,
            "_lastModified": datetime.utcnow().isoformat() + "Z"
        }
    
    def get_aggregate(self, aggregate_id: str) -> Optional[Dict]:
        """Aggregate laden"""
        return self._aggregates.get(aggregate_id)
    
    def log_command(self, command: Command) -> None:
        """Command für Audit-Trail loggen"""
        self._command_log.append(command)
    
    def get_command_history(self, aggregate_id: str) -> List[Command]:
        """Alle Commands für ein Aggregate"""
        return [c for c in self._command_log if c.aggregate_id == aggregate_id]


class ReadModel:
    """
    Read Model - Optimiert für Queries, eventual consistent.
    
    In OpenClaw:
    - Projected Views in memory/views/
    - Search Index via memory_search
    - Optimized für schnelle Queries
    
    Eigenschaften:
    - Denormalisierte Daten
    - Such-Index
    - Eventual Consistency
    """
    
    def __init__(self):
        self._views: Dict[str, Dict] = {}
        self._search_index: Dict[str, List[str]] = {}
        self._query_stats = {"queries": 0, "avg_time_ms": 0}
    
    def project(self, view_id: str, data: Dict, keywords: List[str] = None) -> None:
        """
        Read Model aus Event projizieren.
        
        Verschiedene Projektionen für verschiedene Use Cases:
        - Inbox Summary (zählen, filtern)
        - Detail View (vollständige Daten)
        - Search Index (Keywords)
        """
        self._views[view_id] = {
            **data,
            "_viewId": view_id,
            "_projectedAt": datetime.utcnow().isoformat() + "Z"
        }
        
        # Search Index aktualisieren
        if keywords:
            for keyword in keywords:
                if keyword not in self._search_index:
                    self._search_index[keyword] = []
                if view_id not in self._search_index[keyword]:
                    self._search_index[keyword].append(view_id)
    
    def query_by_id(self, view_id: str) -> Optional[Dict]:
        """Direkte Abfrage nach ID - O(1)"""
        self._query_stats["queries"] += 1
        return self._views.get(view_id)
    
    def query_by_keyword(self, keyword: str) -> List[Dict]:
        """Suche über Index - O(1) Lookup"""
        self._query_stats["queries"] += 1
        view_ids = self._search_index.get(keyword, [])
        return [self._views[vid] for vid in view_ids if vid in self._views]
    
    def query_filtered(self, **filters) -> List[Dict]:
        """Gefilterte Abfrage über alle Views"""
        results = []
        for view in self._views.values():
            match = all(
                view.get(k) == v or (isinstance(v, list) and view.get(k) in v)
                for k, v in filters.items()
            )
            if match:
                results.append(view)
        return results
    
    def get_stats(self) -> Dict:
        """Read Model Statistiken"""
        return {
            "totalViews": len(self._views),
            "indexSize": len(self._search_index),
            "queries": self._query_stats["queries"]
        }


class CQRSStore:
    """
    Kombinierter CQRS Store mit Write und Read Model.
    
    Koordiniert:
    1. Command Handling (Write Side)
    2. Event Publishing
    3. Read Model Projection
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.write_model = WriteModel()
        self.read_model = ReadModel()
        self.event_bus = event_bus or EventBus()
    
    def execute_command(
        self, 
        command: Command, 
        handler: CommandHandler
    ) -> Optional[Event]:
        """
        Command ausführen und Event generieren.
        
        Flow:
        1. Validieren
        2. Business Logic ausführen
        3. Aggregate aktualisieren
        4. Event publishen
        5. Read Model projizieren
        """
        # 1. Validieren
        if not handler.validate(command):
            raise ValueError(f"Command validation failed: {command.command_id}")
        
        # 2. Command loggen
        self.write_model.log_command(command)
        
        # 3. Handler ausführen → Event
        event = handler.handle(command)
        
        # 4. Aggregate aktualisieren
        if command.aggregate_id:
            self.write_model.save_aggregate(
                command.aggregate_id, 
                event.payload
            )
        
        # 5. Event publishen
        self.event_bus.publish(event)
        
        return event
    
    def project_event(self, event: Event, projection_fn: Callable[[Event], Dict]) -> None:
        """
        Manuelle Projection eines Events auf Read Model.
        
        Für komplexe Projektionen, die nicht automatisch sind.
        """
        view_data = projection_fn(event)
        view_id = view_data.get("viewId") or event.payload.get("id")
        keywords = view_data.get("keywords", [])
        
        self.read_model.project(view_id, view_data, keywords)


# ============================================================================
# SAGA PATTERN - Distributed Transaction Coordinator
# ============================================================================

class SagaStatus(Enum):
    """Status einer Saga"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    TIMEOUT = "timeout"


@dataclass
class SagaStep:
    """
    Einzelner Schritt in einer Saga.
    
    Action = Vorwärts-Aktion (Business Logic)
    Compensation = Rückwärts-Aktion bei Fehler
    """
    name: str
    action: Callable[[Dict], Dict]
    compensation: Optional[Callable[[Dict], None]] = None
    max_retries: int = 3
    timeout_seconds: int = 60
    retry_delay_seconds: int = 1


@dataclass
class SagaStepResult:
    """Ergebnis eines Saga-Schritts"""
    step_name: str
    status: str  # success, failed, compensated
    result: Optional[Dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None


class Saga:
    """
    Saga - Koordiniert verteilte Transaktionen.
    
    Pattern: Long-running transaction with compensation
    
    Choreography: Events triggern nächsten Schritt
    Orchestration: Dieser Saga-Manager koordiniert sequentiell
    
    In OpenClaw:
    - Cron Job → Saga State Machine
    - sessions_spawn für AI-Steps
    - exec für Shell-Commands
    """
    
    def __init__(
        self, 
        saga_id: str, 
        name: str, 
        event_bus: Optional[EventBus] = None
    ):
        self.saga_id = saga_id
        self.name = name
        self.event_bus = event_bus
        self.steps: List[SagaStep] = []
        self.current_step = 0
        self.status = SagaStatus.PENDING
        self.context: Dict[str, Any] = {}
        self.step_results: List[SagaStepResult] = []
        self.compensation_log: List[Dict] = []
        self.created_at = datetime.utcnow().isoformat() + "Z"
    
    def add_step(self, step: SagaStep) -> "Saga":
        """Schritt zur Saga hinzufügen (Fluent Interface)"""
        self.steps.append(step)
        return self
    
    def execute(self, initial_context: Dict) -> Dict[str, Any]:
        """
        Saga ausführen mit Compensation bei Fehlern.
        
        Pattern:
        Execute Step 1 → Success? → Execute Step 2
                              └── No → Compensate Step 1
        
        Returns:
            Dict mit Status, Context und Ergebnissen
        """
        self.context = {**initial_context, "saga_id": self.saga_id}
        self.status = SagaStatus.RUNNING
        
        # Saga Started Event
        if self.event_bus:
            self.event_bus.publish(Event.create(
                event_type=EventType.SAGA_STARTED,
                source="saga_orchestrator",
                payload={
                    "sagaId": self.saga_id,
                    "name": self.name,
                    "totalSteps": len(self.steps)
                },
                correlation_id=self.saga_id
            ))
        
        for i, step in enumerate(self.steps):
            self.current_step = i
            
            # Step Started Event
            if self.event_bus:
                self.event_bus.publish(Event.create(
                    event_type=EventType.SAGA_STEP_STARTED,
                    source="saga_orchestrator",
                    payload={
                        "sagaId": self.saga_id,
                        "step": step.name,
                        "stepNumber": i + 1
                    },
                    correlation_id=self.saga_id
                ))
            
            # Schritt ausführen
            result = self._execute_step(step, i)
            self.step_results.append(result)
            
            if result.status == "failed":
                # Compensation starten
                self._compensate(i)
                self.status = SagaStatus.FAILED
                
                if self.event_bus:
                    self.event_bus.publish(Event.create(
                        event_type=EventType.SAGA_STEP_FAILED,
                        source="saga_orchestrator",
                        payload={
                            "sagaId": self.saga_id,
                            "failedStep": step.name,
                            "error": result.error
                        },
                        correlation_id=self.saga_id
                    ))
                
                return {
                    "status": "failed",
                    "failed_step": step.name,
                    "error": result.error,
                    "context": self.context,
                    "step_results": [self._result_to_dict(r) for r in self.step_results]
                }
            
            # Context erweitern
            if result.result:
                self.context.update(result.result)
            
            # Step Completed Event
            if self.event_bus:
                self.event_bus.publish(Event.create(
                    event_type=EventType.SAGA_STEP_COMPLETED,
                    source="saga_orchestrator",
                    payload={
                        "sagaId": self.saga_id,
                        "step": step.name,
                        "stepNumber": i + 1
                    },
                    correlation_id=self.saga_id
                ))
        
        # Alle Schritte erfolgreich
        self.status = SagaStatus.COMPLETED
        
        if self.event_bus:
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
        
        return {
            "status": "completed",
            "context": self.context,
            "step_results": [self._result_to_dict(r) for r in self.step_results]
        }
    
    def _execute_step(self, step: SagaStep, step_index: int) -> SagaStepResult:
        """Einzelnen Schritt mit Retry-Logik ausführen"""
        result = SagaStepResult(step_name=step.name, status="running")
        retry_count = 0
        
        while retry_count < step.max_retries:
            try:
                step_result = step.action(self.context)
                result.status = "success"
                result.result = step_result
                result.retry_count = retry_count
                result.completed_at = datetime.utcnow().isoformat() + "Z"
                return result
                
            except Exception as e:
                retry_count += 1
                if retry_count >= step.max_retries:
                    result.status = "failed"
                    result.error = str(e)
                    result.retry_count = retry_count
                    result.completed_at = datetime.utcnow().isoformat() + "Z"
                    return result
                
                # Exponential Backoff
                import time
                delay = step.retry_delay_seconds * (2 ** retry_count)
                time.sleep(delay)
    
    def _compensate(self, failed_step_index: int) -> None:
        """
        Compensation - Rückwärts-Ausführung bei Fehlern.
        
        Pattern: Fehler in Schritt N → Kompensiere Schritt N-1, N-2, ...
        """
        self.status = SagaStatus.COMPENSATING
        
        if self.event_bus:
            self.event_bus.publish(Event.create(
                event_type=EventType.SAGA_COMPENSATING,
                source="saga_orchestrator",
                payload={
                    "sagaId": self.saga_id,
                    "failedStep": self.steps[failed_step_index].name,
                    "stepsToCompensate": failed_step_index
                },
                correlation_id=self.saga_id
            ))
        
        # Rückwärts durchlaufen
        for i in range(failed_step_index - 1, -1, -1):
            step = self.steps[i]
            if step.compensation:
                try:
                    step.compensation(self.context)
                    self.compensation_log.append({
                        "step": step.name,
                        "status": "compensated",
                        "at": datetime.utcnow().isoformat() + "Z"
                    })
                except Exception as e:
                    self.compensation_log.append({
                        "step": step.name,
                        "status": "failed",
                        "error": str(e),
                        "at": datetime.utcnow().isoformat() + "Z"
                    })
        
        self.status = SagaStatus.COMPENSATED
        
        if self.event_bus:
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
    
    def _result_to_dict(self, result: SagaStepResult) -> Dict:
        """Serialisierung für Rückgabe"""
        return {
            "step_name": result.step_name,
            "status": result.status,
            "result": result.result,
            "error": result.error,
            "retry_count": result.retry_count,
            "started_at": result.started_at,
            "completed_at": result.completed_at
        }
    
    def to_dict(self) -> Dict:
        """Saga State für Persistierung"""
        return {
            "sagaId": self.saga_id,
            "name": self.name,
            "status": self.status.value,
            "currentStep": self.current_step,
            "totalSteps": len(self.steps),
            "context": self.context,
            "stepResults": [self._result_to_dict(r) for r in self.step_results],
            "compensationLog": self.compensation_log,
            "createdAt": self.created_at
        }


# ============================================================================
# SAGA ORCHESTRATOR - Manager für multiple Sagas
# ============================================================================

class SagaOrchestrator:
    """
    Zentraler Manager für alle Sagas.
    
    Verwaltet:
    - Saga Registry (laufende Sagas)
    - Saga State Persistence
    - Recovery bei Crashes
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()
        self._active_sagas: Dict[str, Saga] = {}
        self._completed_sagas: List[Dict] = []
    
    def register_saga(self, saga: Saga) -> str:
        """Saga registrieren und ID zurückgeben"""
        self._active_sagas[saga.saga_id] = saga
        return saga.saga_id
    
    def execute_saga(
        self, 
        saga: Saga, 
        context: Dict
    ) -> Dict[str, Any]:
        """Saga ausführen und verwalten"""
        self.register_saga(saga)
        
        result = saga.execute(context)
        
        # Nach Abschluss verschieben
        if result["status"] in ["completed", "failed"]:
            self._completed_sagas.append(saga.to_dict())
            del self._active_sagas[saga.saga_id]
        
        return result
    
    def get_saga_status(self, saga_id: str) -> Optional[Dict]:
        """Status einer Saga abfragen"""
        if saga_id in self._active_sagas:
            return self._active_sagas[saga_id].to_dict()
        
        # In completed suchen
        for saga in self._completed_sagas:
            if saga["sagaId"] == saga_id:
                return saga
        
        return None
    
    def get_active_sagas(self) -> List[Dict]:
        """Alle aktiven Sagas"""
        return [s.to_dict() for s in self._active_sagas.values()]
    
    def get_stats(self) -> Dict:
        """Orchestrator Statistiken"""
        return {
            "activeSagas": len(self._active_sagas),
            "completedSagas": len(self._completed_sagas),
            "totalSagas": len(self._active_sagas) + len(self._completed_sagas)
        }
