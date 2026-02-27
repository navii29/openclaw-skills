"""
OpenClaw Patterns - CQRS Implementation
Command Query Responsibility Segregation
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from abc import ABC, abstractmethod


class Command:
    """Base Command Class"""
    
    def __init__(
        self,
        command_type: str,
        aggregate_id: str,
        payload: Dict,
        command_id: Optional[str] = None
    ):
        self.command_id = command_id or str(uuid.uuid4())
        self.command_type = command_type
        self.aggregate_id = aggregate_id
        self.payload = payload
        self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict:
        return {
            "commandId": self.command_id,
            "commandType": self.command_type,
            "aggregateId": self.aggregate_id,
            "payload": self.payload,
            "timestamp": self.timestamp
        }


class CommandHandler(ABC):
    """Abstract Base Class für Command Handler"""
    
    @abstractmethod
    def handle(self, command: Command) -> Dict:
        pass
    
    @abstractmethod
    def validate(self, command: Command) -> bool:
        pass


class CommandBus:
    """
    Command Bus für CQRS
    - Route Commands zu Handlern
    - Logging & Audit Trail
    """
    
    def __init__(self, log_path: str = "memory/commands"):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        self._handlers: Dict[str, CommandHandler] = {}
    
    def register(self, command_type: str, handler: CommandHandler):
        """Handler für Command-Typ registrieren"""
        self._handlers[command_type] = handler
    
    def execute(self, command: Command) -> Dict:
        """
        Command ausführen
        """
        # Command loggen
        self._log_command(command)
        
        # Handler finden
        handler = self._handlers.get(command.command_type)
        if not handler:
            raise ValueError(f"No handler for command type: {command.command_type}")
        
        # Validieren
        if not handler.validate(command):
            raise ValueError(f"Command validation failed: {command.command_type}")
        
        # Ausführen
        result = handler.handle(command)
        
        # Ergebnis loggen
        self._log_result(command, result)
        
        return result
    
    def _log_command(self, command: Command):
        log_file = self.log_path / f"{command.command_id}.json"
        with open(log_file, 'w') as f:
            json.dump(command.to_dict(), f, indent=2)
    
    def _log_result(self, command: Command, result: Dict):
        log_file = self.log_path / f"{command.command_id}-result.json"
        with open(log_file, 'w') as f:
            json.dump({
                "commandId": command.command_id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }, f, indent=2)


class ReadModel:
    """
    Read Model für CQRS
    - Optimiert für Queries
    - Denormalized Views
    """
    
    def __init__(self, views_path: str = "memory/views"):
        self.views_path = Path(views_path)
        self.views_path.mkdir(parents=True, exist_ok=True)
    
    def save_view(self, view_name: str, view_id: str, data: Dict):
        """View speichern"""
        view_dir = self.views_path / view_name
        view_dir.mkdir(exist_ok=True)
        
        view_file = view_dir / f"{view_id}.json"
        with open(view_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_view(self, view_name: str, view_id: str) -> Optional[Dict]:
        """Einzelne View laden"""
        view_file = self.views_path / view_name / f"{view_id}.json"
        if view_file.exists():
            with open(view_file) as f:
                return json.load(f)
        return None
    
    def list_views(self, view_name: str) -> List[Dict]:
        """Alle Views eines Typs listen"""
        view_dir = self.views_path / view_name
        if not view_dir.exists():
            return []
        
        views = []
        for view_file in view_dir.glob("*.json"):
            with open(view_file) as f:
                views.append(json.load(f))
        return views
    
    def query_views(
        self,
        view_name: str,
        filter_fn: Optional[callable] = None
    ) -> List[Dict]:
        """Views mit Filter abfragen"""
        views = self.list_views(view_name)
        if filter_fn:
            views = [v for v in views if filter_fn(v)]
        return views


class Projection(ABC):
    """
    Projection: Event → Read Model
    """
    
    def __init__(self, read_model: ReadModel):
        self.read_model = read_model
    
    @abstractmethod
    def project(self, event: Dict) -> Optional[Dict]:
        """Event in View transformieren"""
        pass
    
    def apply(self, event: Dict):
        """Projection anwenden"""
        view_data = self.project(event)
        if view_data:
            self._save_view(event, view_data)
    
    @abstractmethod
    def _save_view(self, event: Dict, view_data: Dict):
        pass


class Aggregate:
    """
    Aggregate Root für CQRS
    - Kapselt Business-Logik
    - Erzeugt Domain Events
    """
    
    def __init__(self, aggregate_id: str, aggregate_type: str):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = 0
        self.uncommitted_events: List[Dict] = []
    
    def apply_event(self, event: Dict):
        """Event auf Aggregate anwenden"""
        handler = getattr(self, f"_on_{event['eventType'].replace('.', '_')}", None)
        if handler:
            handler(event)
        self.version += 1
    
    def create_event(self, event_type: str, payload: Dict) -> Dict:
        """Neues Event erstellen"""
        event = {
            "eventId": str(uuid.uuid4()),
            "eventType": event_type,
            "aggregateId": self.aggregate_id,
            "aggregateType": self.aggregate_type,
            "version": self.version + 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": payload
        }
        self.uncommitted_events.append(event)
        return event


class CQRSStore:
    """
    Kombinierter CQRS Store
    - Commands schreiben
    - Events persistieren
    - Views projizieren
    """
    
    def __init__(self):
        self.command_bus = CommandBus()
        self.read_model = ReadModel()
        self.aggregates_path = Path("memory/aggregates")
        self.aggregates_path.mkdir(parents=True, exist_ok=True)
    
    def execute_command(self, command: Command) -> Dict:
        """Command ausführen"""
        return self.command_bus.execute(command)
    
    def save_aggregate(self, aggregate: Aggregate):
        """Aggregate mit uncommitted events speichern"""
        aggregate_dir = self.aggregates_path / aggregate.aggregate_type
        aggregate_dir.mkdir(exist_ok=True)
        
        # Aggregate State speichern
        state_file = aggregate_dir / f"{aggregate.aggregate_id}.json"
        with open(state_file, 'w') as f:
            json.dump({
                "aggregateId": aggregate.aggregate_id,
                "aggregateType": aggregate.aggregate_type,
                "version": aggregate.version
            }, f, indent=2)
        
        # Events speichern
        events_dir = aggregate_dir / "events"
        events_dir.mkdir(exist_ok=True)
        
        for event in aggregate.uncommitted_events:
            event_file = events_dir / f"{event['eventId']}.json"
            with open(event_file, 'w') as f:
                json.dump(event, f, indent=2)
        
        # Clear uncommitted
        aggregate.uncommitted_events = []
    
    def get_aggregate(self, aggregate_type: str, aggregate_id: str) -> Optional[Dict]:
        """Aggregate laden"""
        state_file = self.aggregates_path / aggregate_type / f"{aggregate_id}.json"
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return None
