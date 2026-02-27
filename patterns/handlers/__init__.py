"""
Event Handlers
==============

Reaktive Komponenten, die auf Events reagieren.

Pattern: Event → Handler → Side Effect

Author: Deep-Dive Session 2026-02-25
"""

from typing import Dict, Any
from patterns.core import Event, EventType, EventBus


class NotificationHandler:
    """
    Handler für Benachrichtigungen.
    
    Reagiert auf:
    - EMAIL_ROUTED → Sendet Notifications basierend auf Priorität
    - SAGA_COMPLETED → Bestätigungsnachrichten
    - SAGA_COMPENSATED → Alert bei Fehlern
    """
    
    def __init__(self, event_bus: EventBus, telegram_chat_id: str = None):
        self.event_bus = event_bus
        self.telegram_chat_id = telegram_chat_id
        self._subscribe()
    
    def _subscribe(self) -> None:
        """Auf Events subscriben"""
        self.event_bus.subscribe(EventType.EMAIL_ROUTED, self.on_email_routed)
        self.event_bus.subscribe(EventType.SAGA_COMPLETED, self.on_saga_completed)
        self.event_bus.subscribe(EventType.SAGA_COMPENSATED, self.on_saga_failed)
        self.event_bus.subscribe(EventType.LEAD_CREATED, self.on_lead_created)
    
    def on_email_routed(self, event: Event) -> None:
        """Reagiere auf Email Routing"""
        decision = event.payload.get("decision", {})
        urgency = decision.get("urgency", "normal")
        
        if urgency == "high":
            print(f"  🔔 HIGH PRIORITY: Sending notification")
            # In Produktion: message.send()
            self._send_notification(
                title="🎯 High-Priority Email",
                message=f"Category: {event.payload.get('category')}"
            )
    
    def on_saga_completed(self, event: Event) -> None:
        """Reagiere auf Saga Completion"""
        print(f"  ✅ Saga completed: {event.payload.get('name')}")
        
        # Metrics logging
        self._log_metric("saga_completed", 1, {
            "saga_name": event.payload.get("name")
        })
    
    def on_saga_failed(self, event: Event) -> None:
        """Reagiere auf Saga Failure"""
        print(f"  ⚠️  SAGA FAILED: Alerting admin")
        
        self._send_notification(
            title="🚨 Saga Failed",
            message=f"Failed Step: {event.payload.get('failedStep')}"
        )
    
    def on_lead_created(self, event: Event) -> None:
        """Reagiere auf neuen Lead"""
        print(f"  🎯 New Lead: {event.payload.get('sender')}")
        
        self._send_notification(
            title="🎯 New Lead Created",
            message=f"From: {event.payload.get('sender')}"
        )
    
    def _send_notification(self, title: str, message: str) -> None:
        """Notification senden (stub für Integration)"""
        # In Produktion: message.send() oder Telegram API
        print(f"    [Notification] {title}: {message}")
    
    def _log_metric(self, name: str, value: float, tags: Dict = None) -> None:
        """Metric loggen"""
        print(f"    [Metric] {name}: {value} {tags or {}}")


class AnalyticsHandler:
    """
    Handler für Analytics und Monitoring.
    
    Sammelt:
    - Event-Statistiken
    - Performance-Metriken
    - Success/Failure-Raten
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.stats = {
            "emailsProcessed": 0,
            "emailsFailed": 0,
            "sagasCompleted": 0,
            "sagasFailed": 0,
            "compensations": 0,
            "leadsCreated": 0,
            "categories": {}
        }
        self._subscribe()
    
    def _subscribe(self) -> None:
        """Auf Events subscriben"""
        self.event_bus.subscribe(EventType.EMAIL_PROCESSED, self.on_email_processed)
        self.event_bus.subscribe(EventType.EMAIL_FAILED, self.on_email_failed)
        self.event_bus.subscribe(EventType.SAGA_COMPLETED, self.on_saga_completed)
        self.event_bus.subscribe(EventType.SAGA_COMPENSATED, self.on_saga_compensated)
        self.event_bus.subscribe(EventType.EMAIL_CATEGORIZED, self.on_email_categorized)
        self.event_bus.subscribe(EventType.LEAD_CREATED, self.on_lead_created)
    
    def on_email_processed(self, event: Event) -> None:
        """Email erfolgreich verarbeitet"""
        self.stats["emailsProcessed"] += 1
    
    def on_email_failed(self, event: Event) -> None:
        """Email-Verarbeitung fehlgeschlagen"""
        self.stats["emailsFailed"] += 1
    
    def on_saga_completed(self, event: Event) -> None:
        """Saga erfolgreich abgeschlossen"""
        self.stats["sagasCompleted"] += 1
    
    def on_saga_compensated(self, event: Event) -> None:
        """Saga kompensiert (fehlgeschlagen)"""
        self.stats["sagasFailed"] += 1
        self.stats["compensations"] += len(
            event.payload.get("compensationLog", [])
        )
    
    def on_email_categorized(self, event: Event) -> None:
        """Email kategorisiert"""
        category = event.payload.get("category", "unknown")
        self.stats["categories"][category] = self.stats["categories"].get(category, 0) + 1
    
    def on_lead_created(self, event: Event) -> None:
        """Neuer Lead erstellt"""
        self.stats["leadsCreated"] += 1
    
    def get_report(self) -> Dict[str, Any]:
        """Analytics Report generieren"""
        total_emails = self.stats["emailsProcessed"] + self.stats["emailsFailed"]
        total_sagas = self.stats["sagasCompleted"] + self.stats["sagasFailed"]
        
        return {
            "summary": self.stats,
            "rates": {
                "emailSuccessRate": self.stats["emailsProcessed"] / max(total_emails, 1),
                "sagaSuccessRate": self.stats["sagasCompleted"] / max(total_sagas, 1),
                "compensationRate": self.stats["compensations"] / max(total_sagas, 1)
            },
            "categoryDistribution": self.stats["categories"]
        }
    
    def print_report(self) -> None:
        """Report auf Konsole ausgeben"""
        report = self.get_report()
        
        print("\n" + "=" * 60)
        print("ANALYTICS REPORT")
        print("=" * 60)
        print(f"Emails Processed: {report['summary']['emailsProcessed']}")
        print(f"Emails Failed: {report['summary']['emailsFailed']}")
        print(f"Sagas Completed: {report['summary']['sagasCompleted']}")
        print(f"Sagas Failed: {report['summary']['sagasFailed']}")
        print(f"Leads Created: {report['summary']['leadsCreated']}")
        print(f"\nSuccess Rates:")
        print(f"  Email: {report['rates']['emailSuccessRate']:.1%}")
        print(f"  Saga: {report['rates']['sagaSuccessRate']:.1%}")
        print(f"\nCategories:")
        for cat, count in report['categoryDistribution'].items():
            print(f"  {cat}: {count}")


class LoggingHandler:
    """
    Handler für Logging aller Events.
    
    Schreibt alle Events in strukturierte Logs für Debugging.
    """
    
    def __init__(self, event_bus: EventBus, log_level: str = "INFO"):
        self.event_bus = event_bus
        self.log_level = log_level
        self._logs: list = []
        self._subscribe()
    
    def _subscribe(self) -> None:
        """Auf alle Events subscriben"""
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self.log_event)
    
    def log_event(self, event: Event) -> None:
        """Event loggen"""
        log_entry = {
            "timestamp": event.timestamp,
            "level": "INFO",
            "eventType": event.event_type.value,
            "source": event.source,
            "correlationId": event.correlation_id[:8],
            "payload_keys": list(event.payload.keys())
        }
        self._logs.append(log_entry)
        
        if self.log_level == "DEBUG":
            print(f"  [LOG] {log_entry['eventType']} from {log_entry['source']}")
    
    def get_logs(self, event_type: EventType = None, limit: int = 100) -> list:
        """Logs filtern und zurückgeben"""
        logs = self._logs
        if event_type:
            logs = [l for l in logs if l["eventType"] == event_type.value]
        return logs[-limit:]
    
    def export_logs(self, path: str) -> None:
        """Logs in Datei exportieren"""
        import json
        with open(path, 'w') as f:
            json.dump(self._logs, f, indent=2)


class AuditHandler:
    """
    Handler für Audit-Trail.
    
    Speichert alle Commands und Events für Compliance.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.audit_trail: list = []
        self._subscribe()
    
    def _subscribe(self) -> None:
        """Auf relevante Events subscriben"""
        self.event_bus.subscribe(EventType.SAGA_STARTED, self.on_saga_started)
        self.event_bus.subscribe(EventType.SAGA_COMPLETED, self.on_saga_completed)
        self.event_bus.subscribe(EventType.SAGA_COMPENSATED, self.on_saga_compensated)
    
    def on_saga_started(self, event: Event) -> None:
        """Saga Start auditieren"""
        self.audit_trail.append({
            "action": "SAGA_STARTED",
            "timestamp": event.timestamp,
            "sagaId": event.payload.get("sagaId"),
            "name": event.payload.get("name"),
            "correlationId": event.correlation_id
        })
    
    def on_saga_completed(self, event: Event) -> None:
        """Saga Completion auditieren"""
        self.audit_trail.append({
            "action": "SAGA_COMPLETED",
            "timestamp": event.timestamp,
            "sagaId": event.payload.get("sagaId"),
            "name": event.payload.get("name"),
            "correlationId": event.correlation_id
        })
    
    def on_saga_compensated(self, event: Event) -> None:
        """Saga Compensation auditieren"""
        self.audit_trail.append({
            "action": "SAGA_COMPENSATED",
            "timestamp": event.timestamp,
            "sagaId": event.payload.get("sagaId"),
            "failedStep": event.payload.get("failedStep"),
            "compensationLog": event.payload.get("compensationLog"),
            "correlationId": event.correlation_id
        })
    
    def get_audit_trail(self, saga_id: str = None) -> list:
        """Audit-Trail abrufen"""
        if saga_id:
            return [e for e in self.audit_trail if e.get("sagaId") == saga_id]
        return self.audit_trail
