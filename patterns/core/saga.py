"""
OpenClaw Patterns - Saga Orchestrator
Saga Pattern for Distributed Transactions
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field


class SagaStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


@dataclass
class SagaStep:
    """Einzelner Saga Schritt"""
    name: str
    action: Callable[[Dict], Dict]
    compensation: Optional[Callable[[Dict], None]] = None
    timeout: int = 60
    retries: int = 3
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class SagaState:
    """Persistierbarer Saga State"""
    saga_id: str
    saga_name: str
    status: SagaStatus
    context: Dict = field(default_factory=dict)
    steps: List[Dict] = field(default_factory=list)
    current_step: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict:
        return {
            "sagaId": self.saga_id,
            "sagaName": self.saga_name,
            "status": self.status.value,
            "context": self.context,
            "steps": self.steps,
            "currentStep": self.current_step,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SagaState':
        return cls(
            saga_id=data["sagaId"],
            saga_name=data["sagaName"],
            status=SagaStatus(data["status"]),
            context=data.get("context", {}),
            steps=data.get("steps", []),
            current_step=data.get("currentStep", 0),
            created_at=data["createdAt"],
            updated_at=data["updatedAt"]
        )


class Saga:
    """
    Saga Definition
    - Choreography oder Orchestration
    - Compensation Chain
    - Idempotency Support
    """
    
    def __init__(self, name: str, saga_id: Optional[str] = None):
        self.name = name
        self.saga_id = saga_id or str(uuid.uuid4())
        self.steps: List[SagaStep] = []
        self.state = SagaState(
            saga_id=self.saga_id,
            saga_name=name,
            status=SagaStatus.PENDING
        )
    
    def add_step(
        self,
        name: str,
        action: Callable[[Dict], Dict],
        compensation: Optional[Callable[[Dict], None]] = None,
        timeout: int = 60,
        retries: int = 3
    ) -> 'Saga':
        """Schritt zur Saga hinzufügen"""
        step = SagaStep(
            name=name,
            action=action,
            compensation=compensation,
            timeout=timeout,
            retries=retries
        )
        self.steps.append(step)
        return self
    
    def execute(self, context: Dict) -> SagaState:
        """
        Saga ausführen
        """
        self.state.context = context
        self.state.status = SagaStatus.RUNNING
        
        try:
            for i, step in enumerate(self.steps):
                self.state.current_step = i
                self._execute_step(step)
            
            self.state.status = SagaStatus.COMPLETED
            
        except Exception as e:
            self.state.status = SagaStatus.FAILED
            # Compensation starten
            self._compensate(i - 1)
        
        return self.state
    
    def _execute_step(self, step: SagaStep):
        """Einzelnen Schritt ausführen mit Retry"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow().isoformat() + "Z"
        
        for attempt in range(step.retries):
            try:
                result = step.action(self.state.context)
                step.result = result
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.utcnow().isoformat() + "Z"
                
                # Context erweitern
                self.state.context[f"{step.name}_result"] = result
                return
                
            except Exception as e:
                if attempt == step.retries - 1:
                    step.error = str(e)
                    step.status = StepStatus.FAILED
                    raise
                # Retry mit kurzem Delay (in echtem System: exponential backoff)
                import time
                time.sleep(0.1 * (2 ** attempt))
    
    def _compensate(self, last_completed_step: int):
        """Compensation Chain ausführen"""
        self.state.status = SagaStatus.COMPENSATING
        
        for i in range(last_completed_step, -1, -1):
            step = self.steps[i]
            if step.compensation:
                step.status = StepStatus.COMPENSATING
                try:
                    step.compensation(self.state.context)
                    step.status = StepStatus.COMPENSATED
                except Exception as e:
                    # Compensation failure loggen (manual intervention needed)
                    print(f"Compensation failed for step {step.name}: {e}")
        
        self.state.status = SagaStatus.COMPENSATED


class SagaOrchestrator:
    """
    Saga Orchestrator für OpenClaw
    - Persistiert Saga State
    - Wiederaufsetzen nach Crash
    - Monitoring & Observability
    """
    
    def __init__(self, state_path: str = "memory/sagas"):
        self.state_path = Path(state_path)
        self.state_path.mkdir(parents=True, exist_ok=True)
        self._saga_definitions: Dict[str, Callable] = {}
    
    def register_saga(self, name: str, saga_factory: Callable):
        """Saga-Definition registrieren"""
        self._saga_definitions[name] = saga_factory
    
    def start_saga(self, saga_name: str, context: Dict) -> str:
        """Neue Saga starten"""
        saga_factory = self._saga_definitions.get(saga_name)
        if not saga_factory:
            raise ValueError(f"Unknown saga: {saga_name}")
        
        saga = saga_factory()
        saga.execute(context)
        
        # State persistieren
        self._save_state(saga.state)
        
        return saga.saga_id
    
    def resume_saga(self, saga_id: str) -> Optional[SagaState]:
        """Saga fortsetzen (nach Crash)"""
        state = self._load_state(saga_id)
        if not state:
            return None
        
        if state.status in [SagaStatus.COMPLETED, SagaStatus.FAILED, SagaStatus.COMPENSATED]:
            return state
        
        # TODO: Fortsetzung implementieren
        return state
    
    def get_saga_status(self, saga_id: str) -> Optional[SagaState]:
        """Saga Status abfragen"""
        return self._load_state(saga_id)
    
    def list_active_sagas(self) -> List[SagaState]:
        """Alle aktiven Sagas listen"""
        active = []
        for state_file in self.state_path.glob("*.json"):
            with open(state_file) as f:
                state = SagaState.from_dict(json.load(f))
                if state.status in [SagaStatus.PENDING, SagaStatus.RUNNING, SagaStatus.COMPENSATING]:
                    active.append(state)
        return active
    
    def _save_state(self, state: SagaState):
        """Saga State persistieren"""
        state.updated_at = datetime.utcnow().isoformat() + "Z"
        state_file = self.state_path / f"{state.saga_id}.json"
        with open(state_file, 'w') as f:
            json.dump(state.to_dict(), f, indent=2)
    
    def _load_state(self, saga_id: str) -> Optional[SagaState]:
        """Saga State laden"""
        state_file = self.state_path / f"{saga_id}.json"
        if state_file.exists():
            with open(state_file) as f:
                return SagaState.from_dict(json.load(f))
        return None


# Convenience Functions
def create_saga(name: str) -> Saga:
    """Neue Saga erstellen"""
    return Saga(name)


def run_saga(
    orchestrator: SagaOrchestrator,
    saga_name: str,
    context: Dict
) -> SagaState:
    """Saga ausführen"""
    saga_id = orchestrator.start_saga(saga_name, context)
    return orchestrator.get_saga_status(saga_id)
