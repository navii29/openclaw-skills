#!/usr/bin/env python3
"""
Notion zu iCal Sync
Export Notion database entries with dates to iCal/ICS format.
"""

import re
import json
import uuid
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class CalendarEvent:
    """Represents a calendar event."""
    uid: str
    summary: str
    start_date: datetime
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    
    @property
    def ical_event(self) -> str:
        """Generate iCal event block."""
        lines = [
            "BEGIN:VEVENT",
            f"UID:{self.uid}",
            f"DTSTAMP:{self._format_datetime(datetime.utcnow())}",
            f"SUMMARY:{self._escape_ical(self.summary)}",
        ]
        
        if self.start_date:
            if self.start_date.hour == 0 and self.start_date.minute == 0:
                # All-day event
                lines.append(f"DTSTART;VALUE=DATE:{self.start_date.strftime('%Y%m%d')}")
            else:
                lines.append(f"DTSTART:{self._format_datetime(self.start_date)}")
        
        if self.end_date:
            if self.end_date.hour == 0 and self.end_date.minute == 0:
                lines.append(f"DTEND;VALUE=DATE:{self.end_date.strftime('%Y%m%d')}")
            else:
                lines.append(f"DTEND:{self._format_datetime(self.end_date)}")
        elif self.start_date and self.start_date.hour == 0:
            # All-day event without end = next day
            next_day = self.start_date + timedelta(days=1)
            lines.append(f"DTEND;VALUE=DATE:{next_day.strftime('%Y%m%d')}")
        
        if self.description:
            lines.append(f"DESCRIPTION:{self._escape_ical(self.description)}")
        
        if self.location:
            lines.append(f"LOCATION:{self._escape_ical(self.location)}")
        
        if self.url:
            lines.append(f"URL:{self.url}")
        
        if self.created:
            lines.append(f"CREATED:{self._format_datetime(self.created)}")
        
        if self.modified:
            lines.append(f"LAST-MODIFIED:{self._format_datetime(self.modified)}")
        
        lines.append("END:VEVENT")
        
        return "\r\n".join(lines)
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for iCal (UTC)."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=__import__('datetime').timezone.utc)
        return dt.strftime('%Y%m%dT%H%M%SZ')
    
    def _escape_ical(self, text: str) -> str:
        """Escape special characters for iCal."""
        return text.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n').replace('\r', '')


class NotionClient:
    """Notion API client."""
    
    BASE_URL = "https://api.notion.com/v1"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def query_database(self, database_id: str, filter_obj: Optional[Dict] = None) -> List[Dict]:
        """Query all entries from database."""
        results = []
        next_cursor = None
        
        while True:
            payload = {}
            if filter_obj:
                payload["filter"] = filter_obj
            if next_cursor:
                payload["start_cursor"] = next_cursor
            
            response = requests.post(
                f"{self.BASE_URL}/databases/{database_id}/query",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            results.extend(data.get('results', []))
            
            if not data.get('has_more'):
                break
            next_cursor = data.get('next_cursor')
        
        return results
    
    def get_database(self, database_id: str) -> Dict:
        """Get database schema."""
        response = requests.get(
            f"{self.BASE_URL}/databases/{database_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


class NotionToICal:
    """Convert Notion database to iCal format."""
    
    def __init__(self, notion_token: str):
        self.notion = NotionClient(notion_token)
    
    def find_date_fields(self, database: Dict) -> List[str]:
        """Find all date fields in database schema."""
        date_fields = []
        properties = database.get('properties', {})
        
        for name, prop in properties.items():
            if prop.get('type') in ['date', 'created_time', 'last_edited_time']:
                date_fields.append(name)
        
        return date_fields
    
    def extract_date(self, page: Dict, field_name: str) -> Optional[datetime]:
        """Extract date from page property."""
        properties = page.get('properties', {})
        prop = properties.get(field_name, {})
        prop_type = prop.get('type', '')
        
        if prop_type == 'date':
            date_data = prop.get('date', {})
            if date_data and date_data.get('start'):
                try:
                    # Try datetime format first
                    return datetime.fromisoformat(date_data['start'].replace('Z', '+00:00'))
                except:
                    # Try date only format
                    try:
                        return datetime.strptime(date_data['start'], '%Y-%m-%d')
                    except:
                        return None
        
        elif prop_type == 'created_time':
            try:
                return datetime.fromisoformat(prop.get('created_time', '').replace('Z', '+00:00'))
            except:
                return None
        
        elif prop_type == 'last_edited_time':
            try:
                return datetime.fromisoformat(prop.get('last_edited_time', '').replace('Z', '+00:00'))
            except:
                return None
        
        return None
    
    def extract_text_property(self, page: Dict, field_name: str) -> Optional[str]:
        """Extract text from page property."""
        properties = page.get('properties', {})
        prop = properties.get(field_name, {})
        prop_type = prop.get('type', '')
        
        if prop_type == 'title':
            items = prop.get('title', [])
            return ''.join(item.get('plain_text', '') for item in items)
        
        elif prop_type == 'rich_text':
            items = prop.get('rich_text', [])
            return ''.join(item.get('plain_text', '') for item in items)
        
        elif prop_type == 'select':
            select = prop.get('select', {})
            return select.get('name', '')
        
        elif prop_type == 'multi_select':
            items = prop.get('multi_select', [])
            return ', '.join(item.get('name', '') for item in items)
        
        return None
    
    def convert_database(self, database_id: str, 
                        title_field: str = "Name",
                        start_date_field: str = "Date",
                        end_date_field: Optional[str] = None,
                        description_fields: Optional[List[str]] = None) -> List[CalendarEvent]:
        """Convert Notion database to calendar events."""
        
        # Get database schema
        database = self.notion.get_database(database_id)
        print(f"📚 Database: {database.get('title', [{}])[0].get('plain_text', 'Untitled')}")
        
        # Find available date fields
        date_fields = self.find_date_fields(database)
        print(f"📅 Date fields found: {', '.join(date_fields) if date_fields else 'None'}")
        
        # Query all entries
        entries = self.notion.query_database(database_id)
        print(f"📄 Found {len(entries)} entries\n")
        
        events = []
        
        for entry in entries:
            # Get title
            title = self.extract_text_property(entry, title_field) or "Untitled"
            
            # Get dates
            start_date = self.extract_date(entry, start_date_field)
            if not start_date:
                continue  # Skip entries without start date
            
            end_date = None
            if end_date_field:
                end_date = self.extract_date(entry, end_date_field)
            
            # Build description
            description_parts = []
            if description_fields:
                for field in description_fields:
                    value = self.extract_text_property(entry, field)
                    if value:
                        description_parts.append(f"{field}: {value}")
            
            # Add Notion URL
            notion_url = entry.get('url', '')
            
            # Create event
            event = CalendarEvent(
                uid=f"notion-{entry.get('id', '').replace('-', '')}@notion-ical",
                summary=title,
                start_date=start_date,
                end_date=end_date,
                description="\n".join(description_parts) if description_parts else None,
                url=notion_url,
                created=self.extract_date(entry, 'Created') if 'Created' in date_fields else None,
                modified=self.extract_date(entry, 'Last edited') if 'Last edited' in date_fields else None
            )
            
            events.append(event)
        
        return events
    
    def generate_ical(self, events: List[CalendarEvent], calendar_name: str = "Notion Calendar") -> str:
        """Generate iCal file content."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Notion iCal Sync//EN",
            f"X-WR-CALNAME:{calendar_name}",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]
        
        for event in events:
            lines.append(event.ical_event)
        
        lines.append("END:VCALENDAR")
        
        return "\r\n".join(lines)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Notion zu iCal Sync')
    parser.add_argument('--token', required=True, help='Notion Integration Token')
    parser.add_argument('--database', required=True, help='Notion Database ID')
    parser.add_argument('--output', '-o', default='notion-calendar.ics', help='Output ICS file')
    parser.add_argument('--title-field', default='Name', help='Field to use as event title')
    parser.add_argument('--date-field', default='Date', help='Field to use as start date')
    parser.add_argument('--end-date-field', help='Field to use as end date')
    parser.add_argument('--description-fields', nargs='+', help='Fields to include in description')
    parser.add_argument('--calendar-name', default='Notion Calendar', help='Calendar name')
    
    args = parser.parse_args()
    
    print("🚀 Notion zu iCal Sync\n")
    
    # Convert
    converter = NotionToICal(args.token)
    
    events = converter.convert_database(
        database_id=args.database,
        title_field=args.title_field,
        start_date_field=args.date_field,
        end_date_field=args.end_date_field,
        description_fields=args.description_fields
    )
    
    if not events:
        print("❌ No events found with dates")
        return
    
    # Generate iCal
    ical_content = converter.generate_ical(events, args.calendar_name)
    
    # Save file
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(ical_content)
    
    print(f"✅ Exported {len(events)} events to {args.output}")
    print(f"📆 Calendar: {args.calendar_name}")
    print(f"\n💡 Import into Google Calendar:")
    print(f"   Settings → Import & Export → Import")


if __name__ == "__main__":
    main()
