"""
OpenClaw Patterns - Core Event Bus
Event-Driven Architecture Implementation
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Callable, Optional
from pathlib import Path

class Event:
    """Standard Event Schema for OpenClaw EDA"""
    
    def __init__(
        self,
        event_type: str,
        payload: Dict,
        source: str,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        event_id: Optional[str] = None
    ):
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.source = source
        self.payload = payload
        self.correlation_id = correlation_id or self.event_id
        self.causation_id = causation_id
        self.metadata = {
            "version": "1.0",
            "retry_count": 0
        }
    
    def to_dict(self) -> Dict:
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "payload": self.payload,
            "correlationId": self.correlation_id,
            "causationId": self.causation_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        event = cls(
            event_type=data["eventType"],
            payload=data["payload"],
            source=data["source"],
            correlation_id=data.get("correlationId"),
            causation_id=data.get("causationId"),
            event_id=data.get("eventId")
        )
        event.timestamp = data["timestamp"]
        event.metadata = data.get("metadata", {})
        return event


class EventBus:
    """
    Event Bus für OpenClaw
    - Publish/Subscribe Pattern
    - Persistent Event Store
    - Correlation Tracking
    """
    
    def __init__(self, store_path: str = "memory/events"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self._handlers: Dict[str, List[Callable]] = {}
        self._global_handlers: List[Callable] = []
    
    def publish(self, event: Event) -> Event:
        """
        Event veröffentlichen und persistieren
        """
        # Event speichern
        event_file = self.store_path / f"{event.event_id}.json"
        with open(event_file, 'w') as f:
            json.dump(event.to_dict(), f, indent=2)
        
        # Handler aufrufen
        self._notify_handlers(event)
        
        return event
    
    def subscribe(self, event_type: str, handler: Callable):
        """
        Auf Event-Typ subscriben
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def subscribe_all(self, handler: Callable):
        """
        Auf alle Events subscriben
        """
        self._global_handlers.append(handler)
    
    def _notify_handlers(self, event: Event):
        """
        Alle relevanten Handler benachrichtigen
        """
        # Globale Handler
        for handler in self._global_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Global handler error: {e}")
        
        # Typ-spezifische Handler
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Handler error for {event.event_type}: {e}")
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Events abfragen (Query Side)
        """
        events = []
        
        for event_file in sorted(self.store_path.glob("*.json"), reverse=True):
            if len(events) >= limit:
                break
            
            try:
                with open(event_file) as f:
                    data = json.load(f)
                    event = Event.from_dict(data)
                    
                    # Filter anwenden
                    if event_type and event.event_type != event_type:
                        continue
                    if correlation_id and event.correlation_id != correlation_id:
                        continue
                    
                    events.append(event)
            except Exception as e:
                print(f"Error loading event {event_file}: {e}")
        
        return events
    
    def get_event_stream(self, correlation_id: str) -> List[Event]:
        """
        Alle Events einer Correlation ID (für Saga Tracking)
        """
        return self.get_events(correlation_id=correlation_id, limit=1000)


# Convenience Functions für OpenClaw Integration
def publish_event(
    event_type: str,
    payload: Dict,
    source: str = "openclaw-patterns",
    correlation_id: Optional[str] = None
) -> Event:
    """
    Kurzform zum Event Publishen
    """
    bus = EventBus()
    event = Event(
        event_type=event_type,
        payload=payload,
        source=source,
        correlation_id=correlation_id
    )
    return bus.publish(event)


def emit_domain_event(
    domain: str,
    action: str,
    aggregate_id: str,
    payload: Dict,
    **kwargs
) -> Event:
    """
    Domain Event im Format domain.action emitieren
    Beispiel: email.received, lead.qualified, invoice.paid
    """
    event_type = f"{domain}.{action}"
    payload_with_id = {**payload, "aggregateId": aggregate_id}
    return publish_event(event_type, payload_with_id, **kwargs)
