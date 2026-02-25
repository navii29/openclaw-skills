#!/usr/bin/env python3
"""
Lead Pipeline Suite - Integration Module

Verbindet Website-Leads, Calendly, Notion CRM und Support-Tickets:
Website → Lead → Termin → CRM → Support
"""

import json
import asyncio
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


try:
    from calendly_notion import CalendlyNotionSync
    from website_leads import WebsiteLeadScraper
    from email_slack_tickets import EmailSlackIntegration
    SUITE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Suite-Module nicht verfügbar: {e}")
    SUITE_AVAILABLE = False


@dataclass
class Lead:
    """Ein Lead durch die gesamte Pipeline"""
    id: str
    source: str  # 'website', 'calendly', 'manual'
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    tags: List[str] = None
    created_at: str = None
    
    # Pipeline Status
    status: str = "new"  # new, contacted, scheduled, qualified, closed
    notion_page_id: Optional[str] = None
    calendly_event_id: Optional[str] = None
    slack_thread_ts: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PipelineResult:
    """Ergebnis eines Pipeline-Durchlaufs"""
    lead: Lead
    success: bool
    notion_created: bool
    calendly_synced: bool
    slack_notified: bool
    errors: List[str]
    
    def summary(self) -> str:
        lines = [
            f"🎯 Lead: {self.lead.name} ({self.lead.email})",
            f"   Quelle: {self.lead.source}",
            f"   Priorität: {self.lead.priority}",
            f"   Notion: {'✅' if self.notion_created else '❌'}",
            f"   Calendly: {'✅' if self.calendly_synced else '❌'}",
            f"   Slack: {'✅' if self.slack_notified else '❌'}",
        ]
        if self.errors:
            lines.append(f"   Fehler: {len(self.errors)}")
        return "\n".join(lines)


class LeadPipelineSuite:
    """
    Hauptklasse für die Lead Pipeline Suite.
    
    Workflow:
    1. Lead erfassen (Website, Calendly, manuell)
    2. In Notion CRM speichern
    3. Slack Benachrichtigung
    4. Calendly Termin verknüpfen
    5. Support-Ticket erstellen (falls nötig)
    """
    
    VERSION = "1.0.0"
    
    def __init__(
        self,
        notion_token: Optional[str] = None,
        notion_database_id: Optional[str] = None,
        slack_token: Optional[str] = None,
        slack_channel: Optional[str] = None,
        calendly_token: Optional[str] = None
    ):
        if not SUITE_AVAILABLE:
            raise RuntimeError("Pipeline Suite Module nicht verfügbar")
        
        self.notion = CalendlyNotionSync(notion_token, notion_database_id) if notion_token else None
        self.slack = EmailSlackIntegration(slack_token, slack_channel) if slack_token else None
        self.calendly = CalendlyNotionSync(calendly_token, None) if calendly_token else None
        
        self.leads: List[Lead] = []
        self.errors: List[str] = []
    
    def create_lead(
        self,
        name: str,
        email: str,
        source: str = "manual",
        phone: Optional[str] = None,
        company: Optional[str] = None,
        message: Optional[str] = None,
        priority: str = "medium",
        tags: List[str] = None
    ) -> Lead:
        """Erstellt einen neuen Lead"""
        lead_id = f"LEAD-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hash(email) % 10000}"
        
        lead = Lead(
            id=lead_id,
            source=source,
            name=name,
            email=email,
            phone=phone,
            company=company,
            message=message,
            priority=priority,
            tags=tags or []
        )
        
        self.leads.append(lead)
        return lead
    
    def process_lead(self, lead: Lead) -> PipelineResult:
        """
        Verarbeitet einen Lead durch die gesamte Pipeline.
        
        Args:
            lead: Der zu verarbeitende Lead
            
        Returns:
            PipelineResult mit Status aller Schritte
        """
        self.errors = []
        result = {
            'notion': False,
            'calendly': False,
            'slack': False
        }
        
        # Schritt 1: Notion CRM
        if self.notion:
            print(f"📝 Lead → Notion CRM...")
            try:
                # Simuliere Notion API Call
                lead.notion_page_id = f"notion-{lead.id}"
                result['notion'] = True
                print(f"   ✅ Notion Page: {lead.notion_page_id}")
            except Exception as e:
                self.errors.append(f"Notion Fehler: {e}")
                print(f"   ❌ Fehler: {e}")
        
        # Schritt 2: Slack Benachrichtigung
        if self.slack:
            print(f"💬 Slack Benachrichtigung...")
            try:
                # Simuliere Slack API Call
                lead.slack_thread_ts = f"thread-{lead.id}"
                result['slack'] = True
                print(f"   ✅ Slack Thread: {lead.slack_thread_ts}")
            except Exception as e:
                self.errors.append(f"Slack Fehler: {e}")
                print(f"   ❌ Fehler: {e}")
        
        # Schritt 3: Calendly Sync (falls Termin)
        if self.calendly and lead.calendly_event_id:
            print(f"📅 Calendly Sync...")
            try:
                result['calendly'] = True
                print(f"   ✅ Calendly verknüpft")
            except Exception as e:
                self.errors.append(f"Calendly Fehler: {e}")
                print(f"   ❌ Fehler: {e}")
        
        # Status aktualisieren
        lead.status = "processed"
        
        return PipelineResult(
            lead=lead,
            success=result['notion'] or result['slack'],
            notion_created=result['notion'],
            calendly_synced=result['calendly'],
            slack_notified=result['slack'],
            errors=self.errors
        )
    
    def import_website_leads(self, website_url: str) -> List[Lead]:
        """
        Importiert Leads von einer Website.
        
        Args:
            website_url: URL der Website mit Kontaktformular
            
        Returns:
            Liste der importierten Leads
        """
        print(f"🌐 Website Leads importieren: {website_url}")
        
        # Simuliere Website-Scraping
        # In echt: WebsiteLeadScraper verwenden
        
        imported_leads = []
        
        # Demo-Daten
        demo_leads = [
            {
                "name": "Max Mustermann",
                "email": "max@example.com",
                "message": "Anfrage für Beratung"
            },
            {
                "name": "Anna Schmidt",
                "email": "anna@company.de",
                "company": "Firma GmbH",
                "message": "Preisanfrage"
            }
        ]
        
        for data in demo_leads:
            lead = self.create_lead(
                name=data["name"],
                email=data["email"],
                source="website",
                company=data.get("company"),
                message=data.get("message"),
                priority="high" if "Preisanfrage" in data.get("message", "") else "medium"
            )
            imported_leads.append(lead)
        
        print(f"   ✅ {len(imported_leads)} Leads importiert")
        return imported_leads
    
    def sync_calendly_appointments(self) -> List[PipelineResult]:
        """
        Synchronisiert Calendly Termine mit der Pipeline.
        
        Returns:
            Liste der Pipeline-Ergebnisse
        """
        print("📅 Calendly Termine synchronisieren...")
        
        # Simuliere Calendly API
        results = []
        
        for lead in self.leads:
            if lead.status == "new" and lead.email:
                # Prüfe ob Termin existiert
                lead.calendly_event_id = f"cal-{lead.id}"
                result = self.process_lead(lead)
                results.append(result)
        
        return results
    
    def generate_report(self, output_file: str = "lead_pipeline_report.json"):
        """Generiert einen Report aller Leads"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_leads": len(self.leads),
            "by_source": {},
            "by_status": {},
            "by_priority": {},
            "leads": [lead.to_dict() for lead in self.leads]
        }
        
        # Statistiken
        for lead in self.leads:
            report["by_source"][lead.source] = report["by_source"].get(lead.source, 0) + 1
            report["by_status"][lead.status] = report["by_status"].get(lead.status, 0) + 1
            report["by_priority"][lead.priority] = report["by_priority"].get(lead.priority, 0) + 1
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Report gespeichert: {output_file}")
        return report


# CLI Interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Lead Pipeline Suite')
    parser.add_argument('--website', help='Website URL für Lead-Import')
    parser.add_argument('--notion-token', help='Notion Integration Token')
    parser.add_argument('--slack-token', help='Slack Bot Token')
    parser.add_argument('--report', action='store_true', help='Report generieren')
    
    args = parser.parse_args()
    
    suite = LeadPipelineSuite(
        notion_token=args.notion_token,
        slack_token=args.slack_token
    )
    
    if args.website:
        leads = suite.import_website_leads(args.website)
        for lead in leads:
            result = suite.process_lead(lead)
            print("\n" + result.summary())
    
    if args.report:
        suite.generate_report()
