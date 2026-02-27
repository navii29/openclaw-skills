"""
Email Processing Saga
Kombiniert EDA, CQRS und Saga Pattern
"""
import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace')

from patterns.core.event_bus import EventBus, Event, emit_domain_event
from patterns.core.cqrs import CQRSStore, Command, CommandHandler, Aggregate
from patterns.core.saga import SagaOrchestrator, Saga, SagaState
from datetime import datetime
from typing import Dict


# =============================================================================
# EMAIL AGGREGATE (CQRS)
# =============================================================================

class EmailAggregate(Aggregate):
    """Email als CQRS Aggregate"""
    
    def __init__(self, email_id: str):
        super().__init__(email_id, "email")
        self.subject = ""
        self.sender = ""
        self.body = ""
        self.category = None
        self.priority = None
        self.status = "received"
    
    def receive(self, subject: str, sender: str, body: str):
        """Command: Email empfangen"""
        event = self.create_event("email.received", {
            "subject": subject,
            "sender": sender,
            "body_preview": body[:200],
            "receivedAt": datetime.utcnow().isoformat() + "Z"
        })
        self.apply_event(event)
        return event
    
    def categorize(self, category: str, confidence: float):
        """Command: Email kategorisieren"""
        event = self.create_event("email.categorized", {
            "category": category,
            "confidence": confidence,
            "categorizedAt": datetime.utcnow().isoformat() + "Z"
        })
        self.apply_event(event)
        return event
    
    def prioritize(self, priority: str, reason: str):
        """Command: Priorität setzen"""
        event = self.create_event("email.prioritized", {
            "priority": priority,
            "reason": reason
        })
        self.apply_event(event)
        return event
    
    def route(self, destination: str, action: str):
        """Command: Email routen"""
        event = self.create_event("email.routed", {
            "destination": destination,
            "action": action,
            "routedAt": datetime.utcnow().isoformat() + "Z"
        })
        self.apply_event(event)
        return event
    
    # Event Handlers
    def _on_email_received(self, event):
        self.subject = event['payload']['subject']
        self.sender = event['payload']['sender']
        self.status = "received"
    
    def _on_email_categorized(self, event):
        self.category = event['payload']['category']
        self.status = "categorized"
    
    def _on_email_prioritized(self, event):
        self.priority = event['payload']['priority']
        self.status = "prioritized"
    
    def _on_email_routed(self, event):
        self.status = "routed"


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

class ReceiveEmailHandler(CommandHandler):
    def validate(self, command: Command) -> bool:
        return all(k in command.payload for k in ['subject', 'sender', 'body'])
    
    def handle(self, command: Command) -> Dict:
        email = EmailAggregate(command.aggregate_id)
        event = email.receive(
            command.payload['subject'],
            command.payload['sender'],
            command.payload['body']
        )
        return {"eventId": event['eventId'], "status": "received"}


class CategorizeEmailHandler(CommandHandler):
    def validate(self, command: Command) -> bool:
        return 'category' in command.payload
    
    def handle(self, command: Command) -> Dict:
        email = EmailAggregate(command.aggregate_id)
        event = email.categorize(
            command.payload['category'],
            command.payload.get('confidence', 0.9)
        )
        return {"eventId": event['eventId'], "category": command.payload['category']}


# =============================================================================
# EMAIL PROCESSING SAGA
# =============================================================================

def create_email_processing_saga() -> Saga:
    """
    Factory für Email Processing Saga
    5 Schritte: Extract → Categorize → Prioritize → Route → Execute
    """
    saga = Saga("email-processing")
    
    # Step 1: Extract Email
    saga.add_step(
        name="extract",
        action=_step_extract,
        compensation=_compensate_extract,
        timeout=30,
        retries=3
    )
    
    # Step 2: Categorize
    saga.add_step(
        name="categorize",
        action=_step_categorize,
        compensation=_compensate_categorize,
        timeout=60,
        retries=2
    )
    
    # Step 3: Prioritize
    saga.add_step(
        name="prioritize",
        action=_step_prioritize,
        compensation=_compensate_prioritize,
        timeout=30,
        retries=2
    )
    
    # Step 4: Route
    saga.add_step(
        name="route",
        action=_step_route,
        compensation=_compensate_route,
        timeout=10,
        retries=1
    )
    
    # Step 5: Execute Action
    saga.add_step(
        name="execute",
        action=_step_execute,
        compensation=None,  # Final step, no compensation needed
        timeout=30,
        retries=1
    )
    
    return saga


def _step_extract(context: Dict) -> Dict:
    """Step 1: Email aus IMAP extrahieren"""
    email_id = context['email_id']
    print(f"  📥 [Extract] Email {email_id} wird extrahiert...")
    
    # Simulation
    return {
        "email_id": email_id,
        "subject": context.get('subject', 'Re: Anfrage Automation'),
        "sender": context.get('sender', 'kunde@beispiel.de'),
        "body": "Hallo, ich interessiere mich für Ihre Automation-Dienste...",
        "extracted_at": datetime.utcnow().isoformat()
    }


def _compensate_extract(context: Dict):
    """Compensation: Email als ungelesen markieren"""
    print(f"  ↩️  [Compensate Extract] Email {context['email_id']} als ungelesen markiert")


def _step_categorize(context: Dict) -> Dict:
    """Step 2: Email mit AI kategorisieren"""
    print(f"  🧠 [Categorize] Kategorisiere Email...")
    
    # AI-Kategorisierung (simuliert)
    sender = context.get('sender', '')
    subject = context.get('subject', '')
    
    if 'angebot' in subject.lower() or 'kauf' in subject.lower():
        category = "lead"
        confidence = 0.95
    elif 'rechnung' in subject.lower():
        category = "invoice"
        confidence = 0.98
    elif 'support' in subject.lower() or 'hilfe' in subject.lower():
        category = "support"
        confidence = 0.90
    else:
        category = "general"
        confidence = 0.75
    
    print(f"     → Kategorie: {category.upper()} (Confidence: {confidence:.0%})")
    
    return {
        "category": category,
        "confidence": confidence,
        "categorized_at": datetime.utcnow().isoformat()
    }


def _compensate_categorize(context: Dict):
    """Compensation: Kategorie zurücksetzen"""
    print(f"  ↩️  [Compensate Categorize] Kategorie zurückgesetzt")


def _step_prioritize(context: Dict) -> Dict:
    """Step 3: Priorisierung basierend auf Kategorie"""
    category = context.get('categorize_result', {}).get('category', 'general')
    
    print(f"  ⚡ [Prioritize] Priorisiere Email...")
    
    if category == "lead":
        priority = "HIGH"
        reason = "Potential customer inquiry"
    elif category == "invoice":
        priority = "HIGH"
        reason = "Payment related"
    elif category == "support":
        priority = "MEDIUM"
        reason = "Customer support request"
    else:
        priority = "LOW"
        reason = "General inquiry"
    
    print(f"     → Priorität: {priority} ({reason})")
    
    return {
        "priority": priority,
        "reason": reason
    }


def _compensate_prioritize(context: Dict):
    """Compensation: Priorität zurücksetzen"""
    print(f"  ↩️  [Compensate Prioritize] Priorität zurückgesetzt")


def _step_route(context: Dict) -> Dict:
    """Step 4: Routing basierend auf Kategorie und Priorität"""
    category = context.get('categorize_result', {}).get('category', 'general')
    priority = context.get('prioritize_result', {}).get('priority', 'LOW')
    
    print(f"  🎯 [Route] Route Email...")
    
    if category == "lead" and priority == "HIGH":
        destination = "sales-immediate"
        action = "create_hubspot_deal"
    elif category == "lead":
        destination = "sales-nurture"
        action = "add_to_nurture_sequence"
    elif category == "invoice":
        destination = "accounting"
        action = "process_invoice"
    elif category == "support":
        destination = "support-queue"
        action = "create_ticket"
    else:
        destination = "archive"
        action = "auto_reply"
    
    print(f"     → Route zu: {destination} | Aktion: {action}")
    
    return {
        "destination": destination,
        "action": action
    }


def _compensate_route(context: Dict):
    """Compensation: Routing rückgängig machen"""
    print(f"  ↩️  [Compensate Route] Routing rückgängig gemacht")


def _step_execute(context: Dict) -> Dict:
    """Step 5: Finale Aktion ausführen"""
    route_result = context.get('route_result', {})
    action = route_result.get('action', 'archive')
    destination = route_result.get('destination', 'archive')
    
    print(f"  ✅ [Execute] Führe Aktion aus: {action}")
    
    # Aktion simulieren
    result = {
        "action": action,
        "destination": destination,
        "executed_at": datetime.utcnow().isoformat(),
        "success": True
    }
    
    print(f"     → Aktion erfolgreich ausgeführt!")
    
    return result


# =============================================================================
# EVENT HANDLERS (EDA)
# =============================================================================

def on_email_received(event):
    """Handler für email.received Events"""
    payload = event.payload if hasattr(event, 'payload') else event.get('payload', {})
    sender = payload.get('sender', 'unknown') if isinstance(payload, dict) else 'unknown'
    print(f"📧 Event Handler: Neue Email empfangen von {sender}")


def on_email_categorized(event):
    """Handler für email.categorized Events"""
    payload = event.payload if hasattr(event, 'payload') else event.get('payload', {})
    category = payload.get('category', 'unknown') if isinstance(payload, dict) else 'unknown'
    print(f"🏷️  Event Handler: Email kategorisiert als {category}")


def on_email_routed(event):
    """Handler für email.routed Events"""
    payload = event.payload if hasattr(event, 'payload') else event.get('payload', {})
    destination = payload.get('destination', 'unknown') if isinstance(payload, dict) else 'unknown'
    print(f"🎯 Event Handler: Email geroutet zu {destination}")


# =============================================================================
# INITIALISIERUNG
# =============================================================================

def initialize_orchestrator() -> SagaOrchestrator:
    """Orchestrator mit Email Processing Saga initialisieren"""
    orchestrator = SagaOrchestrator()
    orchestrator.register_saga("email-processing", create_email_processing_saga)
    return orchestrator


def initialize_event_bus() -> EventBus:
    """Event Bus mit Handlern initialisieren"""
    bus = EventBus()
    bus.subscribe("email.received", on_email_received)
    bus.subscribe("email.categorized", on_email_categorized)
    bus.subscribe("email.routed", on_email_routed)
    return bus
