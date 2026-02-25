#!/usr/bin/env python3
"""Test Notion zu iCal Sync"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/notion-ical-sync')

from datetime import datetime
from notion_ical import CalendarEvent, NotionToICal

def run_tests():
    """Test iCal generation without real API calls."""
    print("🧪 Testing Notion zu iCal Sync...\n")
    
    # Test 1: CalendarEvent creation
    print("Test 1: CalendarEvent Erstellung")
    event = CalendarEvent(
        uid="test-123@notion",
        summary="Projekt-Meeting",
        start_date=datetime(2024, 3, 15, 14, 0),
        end_date=datetime(2024, 3, 15, 15, 30),
        description="Wichtiges Team-Meeting",
        url="https://notion.so/page-123"
    )
    
    print(f"   Summary: {event.summary}")
    print(f"   Start: {event.start_date}")
    print(f"   End: {event.end_date}")
    print(f"   UID: {event.uid}")
    
    test1_pass = (
        event.summary == "Projekt-Meeting" and
        event.start_date.hour == 14
    )
    print(f"   Status: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print()
    
    # Test 2: iCal format generation
    print("Test 2: iCal Format Generierung")
    ical = event.ical_event
    
    checks = [
        "BEGIN:VEVENT" in ical,
        "END:VEVENT" in ical,
        "SUMMARY:Projekt-Meeting" in ical,
        "UID:test-123@notion" in ical,
        "DTSTART:20240315T140000Z" in ical,
        "DTEND:20240315T153000Z" in ical,
        "DESCRIPTION:Wichtiges Team-Meeting" in ical
    ]
    
    test2_pass = all(checks)
    print(f"   VEVENT Block: {'✅' if 'BEGIN:VEVENT' in ical else '❌'}")
    print(f"   SUMMARY: {'✅' if 'SUMMARY:Projekt-Meeting' in ical else '❌'}")
    print(f"   DTSTART: {'✅' if 'DTSTART' in ical else '❌'}")
    print(f"   DTEND: {'✅' if 'DTEND' in ical else '❌'}")
    print(f"   Status: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print()
    
    # Test 3: All-day event
    print("Test 3: Ganztägiger Termin")
    all_day = CalendarEvent(
        uid="allday-123@notion",
        summary="Urlaub",
        start_date=datetime(2024, 3, 20),  # No time = all-day
    )
    
    ical_all_day = all_day.ical_event
    all_day_pass = (
        "DTSTART;VALUE=DATE:20240320" in ical_all_day and
        "DTEND;VALUE=DATE:20240321" in ical_all_day
    )
    
    print(f"   All-day start: {'✅' if 'VALUE=DATE' in ical_all_day else '❌'}")
    print(f"   Status: {'✅ PASS' if all_day_pass else '❌ FAIL'}")
    print()
    
    # Test 4: Special character escaping
    print("Test 4: Sonderzeichen Escaping")
    special = CalendarEvent(
        uid="special@notion",
        summary="Meeting;mit,Komma",
        start_date=datetime(2024, 3, 15, 10, 0),
        description="Line 1\nLine 2"
    )
    
    ical_special = special.ical_event
    
    # Check that special chars are escaped
    special_pass = "\\;" in ical_special or "\\," in ical_special or "\\n" in ical_special
    print(f"   Escaping gefunden: {'✅' if special_pass else '❌'}")
    print(f"   Status: {'✅ PASS' if special_pass else '❌ FAIL'}")
    print()
    
    # Test 5: Full calendar generation
    print("Test 5: Vollständiger Kalender-Export")
    converter = NotionToICal("fake-token")
    
    events = [
        CalendarEvent(
            uid="event1@notion",
            summary="Meeting 1",
            start_date=datetime(2024, 3, 15, 9, 0),
            end_date=datetime(2024, 3, 15, 10, 0)
        ),
        CalendarEvent(
            uid="event2@notion",
            summary="Meeting 2",
            start_date=datetime(2024, 3, 16, 14, 0),
            end_date=datetime(2024, 3, 16, 15, 0)
        )
    ]
    
    ical_full = converter.generate_ical(events, "Mein Notion Kalender")
    
    full_checks = [
        "BEGIN:VCALENDAR" in ical_full,
        "END:VCALENDAR" in ical_full,
        "VERSION:2.0" in ical_full,
        "X-WR-CALNAME:Mein Notion Kalender" in ical_full,
        ical_full.count("BEGIN:VEVENT") == 2,
        ical_full.count("END:VEVENT") == 2
    ]
    
    test5_pass = all(full_checks)
    print(f"   VCALENDAR Block: {'✅' if 'BEGIN:VCALENDAR' in ical_full else '❌'}")
    print(f"   2 Events: {'✅' if ical_full.count('BEGIN:VEVENT') == 2 else '❌'}")
    print(f"   Calendar Name: {'✅' if 'X-WR-CALNAME' in ical_full else '❌'}")
    print(f"   Status: {'✅ PASS' if test5_pass else '❌ FAIL'}")
    print()
    
    # Test 6: Date extraction simulation
    print("Test 6: Datum-Extraktion (simuliert)")
    
    # Simulate Notion page structure
    test_page = {
        'properties': {
            'Name': {
                'type': 'title',
                'title': [{'plain_text': 'Projekt Kickoff'}]
            },
            'Date': {
                'type': 'date',
                'date': {'start': '2024-03-20'}
            },
            'Status': {
                'type': 'select',
                'select': {'name': 'In Progress'}
            }
        },
        'url': 'https://notion.so/page-123'
    }
    
    title = converter.extract_text_property(test_page, 'Name')
    status = converter.extract_text_property(test_page, 'Status')
    date = converter.extract_date(test_page, 'Date')
    
    extract_pass = (
        title == 'Projekt Kickoff' and
        status == 'In Progress' and
        date == datetime(2024, 3, 20)
    )
    
    print(f"   Title: {title}")
    print(f"   Status: {status}")
    print(f"   Date: {date}")
    print(f"   Status: {'✅ PASS' if extract_pass else '❌ FAIL'}")
    print()
    
    # Summary
    results = [test1_pass, test2_pass, all_day_pass, special_pass, test5_pass, extract_pass]
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Summary: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Skill is ready for production.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
