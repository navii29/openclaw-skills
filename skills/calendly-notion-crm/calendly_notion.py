#!/usr/bin/env python3
"""
Calendly zu Notion CRM Sync
Sync Calendly appointments to Notion CRM database.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CalendlyEvent:
    """Represents a Calendly scheduled event."""
    uri: str
    name: str
    email: str
    start_time: str
    end_time: str
    status: str
    event_type: str
    location: Optional[str] = None
    questions: Optional[Dict] = None
    
    @property
    def date_formatted(self) -> str:
        """Format date for display."""
        try:
            dt = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y %H:%M')
        except:
            return self.start_time
    
    @property
    def follow_up_date(self) -> str:
        """Calculate follow-up date (3 days after meeting)."""
        try:
            dt = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
            follow_up = dt + timedelta(days=3)
            return follow_up.strftime('%Y-%m-%d')
        except:
            return ""


class CalendlyClient:
    """Client for Calendly API."""
    
    BASE_URL = "https://api.calendly.com"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.user_uri = None
    
    def get_user(self) -> Optional[str]:
        """Get current user URI."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/users/me",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            self.user_uri = data['resource']['uri']
            return self.user_uri
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_events(self, days_back: int = 30, days_forward: int = 30) -> List[CalendlyEvent]:
        """Get scheduled events."""
        if not self.user_uri:
            self.get_user()
        
        if not self.user_uri:
            return []
        
        # Calculate date range
        min_time = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + 'Z'
        max_time = (datetime.utcnow() + timedelta(days=days_forward)).isoformat() + 'Z'
        
        events = []
        next_page = None
        
        try:
            while True:
                params = {
                    "user": self.user_uri,
                    "min_start_time": min_time,
                    "max_start_time": max_time,
                    "status": "active",
                    "count": 100
                }
                if next_page:
                    params["page_token"] = next_page
                
                response = requests.get(
                    f"{self.BASE_URL}/scheduled_events",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                for event in data.get('collection', []):
                    # Get invitee details
                    invitees = self.get_invitees(event['uri'])
                    for invitee in invitees:
                        cal_event = CalendlyEvent(
                            uri=event['uri'],
                            name=invitee.get('name', 'Unknown'),
                            email=invitee.get('email', ''),
                            start_time=event['start_time'],
                            end_time=event['end_time'],
                            status=event['status'],
                            event_type=event.get('name', 'Meeting'),
                            location=event.get('location', {}).get('join_url') if event.get('location') else None,
                            questions=invitee.get('questions_and_answers', {})
                        )
                        events.append(cal_event)
                
                next_page = data.get('pagination', {}).get('next_page_token')
                if not next_page:
                    break
                    
        except Exception as e:
            print(f"Error fetching events: {e}")
        
        return events
    
    def get_invitees(self, event_uri: str) -> List[Dict]:
        """Get invitees for an event."""
        try:
            response = requests.get(
                f"{event_uri}/invitees",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get('collection', [])
        except Exception as e:
            print(f"Error fetching invitees: {e}")
            return []


class NotionCRM:
    """Notion CRM client."""
    
    BASE_URL = "https://api.notion.com/v1"
    
    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def find_existing_page(self, email: str, start_time: str) -> Optional[str]:
        """Find existing page by email and date."""
        try:
            response = requests.post(
                f"{self.BASE_URL}/databases/{self.database_id}/query",
                headers=self.headers,
                json={
                    "filter": {
                        "and": [
                            {
                                "property": "Email",
                                "email": {
                                    "equals": email
                                }
                            },
                            {
                                "property": "Datum",
                                "date": {
                                    "equals": start_time[:10]
                                }
                            }
                        ]
                    }
                }
            )
            response.raise_for_status()
            results = response.json().get('results', [])
            if results:
                return results[0]['id']
            return None
        except Exception as e:
            print(f"Error finding page: {e}")
            return None
    
    def create_or_update_entry(self, event: CalendlyEvent) -> bool:
        """Create or update CRM entry."""
        try:
            # Check if entry exists
            existing_id = self.find_existing_page(event.email, event.start_time)
            
            # Build properties
            properties = {
                "Name": {
                    "title": [{"text": {"content": event.name}}]
                },
                "Email": {
                    "email": event.email
                },
                "Datum": {
                    "date": {
                        "start": event.start_time[:10]
                    }
                },
                "Uhrzeit": {
                    "rich_text": [{"text": {"content": event.date_formatted.split(' ')[1] if ' ' in event.date_formatted else ''}}]
                },
                "Status": {
                    "select": {
                        "name": self._map_status(event.status)
                    }
                },
                "Event Typ": {
                    "select": {
                        "name": event.event_type[:100]
                    }
                },
                "Follow-up": {
                    "date": {
                        "start": event.follow_up_date
                    }
                }
            }
            
            # Add location/notes if available
            notes = ""
            if event.location:
                notes += f"Meeting Link: {event.location}\n"
            if event.questions:
                for q in event.questions:
                    notes += f"{q.get('question', '')}: {q.get('answer', '')}\n"
            
            if notes:
                properties["Notizen"] = {
                    "rich_text": [{"text": {"content": notes[:2000]}}]
                }
            
            if existing_id:
                # Update existing
                response = requests.patch(
                    f"{self.BASE_URL}/pages/{existing_id}",
                    headers=self.headers,
                    json={"properties": properties}
                )
                print(f"   📝 Updated: {event.name}")
            else:
                # Create new
                response = requests.post(
                    f"{self.BASE_URL}/pages",
                    headers=self.headers,
                    json={
                        "parent": {"database_id": self.database_id},
                        "properties": properties
                    }
                )
                print(f"   ➕ Created: {event.name}")
            
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Error creating entry: {e}")
            return False
    
    def _map_status(self, calendly_status: str) -> str:
        """Map Calendly status to CRM status."""
        status_map = {
            'active': '📅 Geplant',
            'canceled': '❌ Abgesagt',
            'completed': '✅ Stattgefunden'
        }
        return status_map.get(calendly_status, calendly_status)


class CalendlyNotionSync:
    """Main sync orchestrator."""
    
    def __init__(self, calendly_token: str, notion_token: str, notion_db: str):
        self.calendly = CalendlyClient(calendly_token)
        self.notion = NotionCRM(notion_token, notion_db)
    
    def sync(self, days_back: int = 30, days_forward: int = 30) -> Dict:
        """Run full sync."""
        print("🚀 Starting Calendly → Notion Sync\n")
        
        # Get events from Calendly
        print(f"📥 Fetching Calendly events...")
        events = self.calendly.get_events(days_back, days_forward)
        print(f"   Found {len(events)} events\n")
        
        if not events:
            return {"synced": 0, "errors": 0}
        
        # Sync to Notion
        print("📤 Syncing to Notion CRM...")
        synced = 0
        errors = 0
        
        for event in events:
            if self.notion.create_or_update_entry(event):
                synced += 1
            else:
                errors += 1
        
        print(f"\n✅ Sync complete: {synced} synced, {errors} errors")
        
        return {
            "total": len(events),
            "synced": synced,
            "errors": errors
        }


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Calendly zu Notion CRM Sync')
    parser.add_argument('--calendly-token', required=True, help='Calendly API Token')
    parser.add_argument('--notion-token', required=True, help='Notion Integration Token')
    parser.add_argument('--database-id', required=True, help='Notion Database ID')
    parser.add_argument('--days-back', type=int, default=30, help='Days to look back')
    parser.add_argument('--days-forward', type=int, default=30, help='Days to look forward')
    
    args = parser.parse_args()
    
    sync = CalendlyNotionSync(
        args.calendly_token,
        args.notion_token,
        args.database_id
    )
    
    result = sync.sync(args.days_back, args.days_forward)
    
    # Save report
    report_file = f"sync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"💾 Report saved: {report_file}")


if __name__ == "__main__":
    main()
