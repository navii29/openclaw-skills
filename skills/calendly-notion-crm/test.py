#!/usr/bin/env python3
"""Test Calendly zu Notion CRM Sync"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/calendly-notion-crm')

from calendly_notion import CalendlyEvent, CalendlyNotionSync

def run_tests():
    """Test data structures and formatting."""
    print("🧪 Testing Calendly zu Notion CRM Sync...\n")
    
    # Test 1: CalendlyEvent dataclass
    print("Test 1: CalendlyEvent Erstellung")
    event = CalendlyEvent(
        uri="https://api.calendly.com/scheduled_events/ABC123",
        name="Max Mustermann",
        email="max@example.de",
        start_time="2024-03-15T14:00:00.000000Z",
        end_time="2024-03-15T15:00:00.000000Z",
        status="active",
        event_type="Erstgespräch 30min",
        location="https://zoom.us/j/123456",
        questions=[
            {"question": "Firma", "answer": "Muster GmbH"},
            {"question": "Thema", "answer": "Website Relaunch"}
        ]
    )
    
    print(f"   Name: {event.name}")
    print(f"   Email: {event.email}")
    print(f"   Datum formatiert: {event.date_formatted}")
    print(f"   Follow-up Datum: {event.follow_up_date}")
    
    test1_pass = (
        event.name == "Max Mustermann" and
        event.email == "max@example.de" and
        event.date_formatted == "15.03.2024 14:00" and
        event.follow_up_date == "2024-03-18"
    )
    print(f"   Status: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print()
    
    # Test 2: Status mapping
    print("Test 2: Status Mapping")
    sync = CalendlyNotionSync("fake", "fake", "fake")
    
    status_tests = [
        ('active', '📅 Geplant'),
        ('canceled', '❌ Abgesagt'),
        ('completed', '✅ Stattgefunden'),
        ('unknown', 'unknown')
    ]
    
    status_pass = True
    for input_status, expected in status_tests:
        result = sync.notion._map_status(input_status)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {input_status} → {result}")
        if result != expected:
            status_pass = False
    print()
    
    # Test 3: Different time formats
    print("Test 3: Zeitformate")
    time_tests = [
        ("2024-01-01T09:30:00.000000Z", "01.01.2024 09:30"),
        ("2024-12-31T23:59:00.000000Z", "31.12.2024 23:59"),
    ]
    
    time_pass = True
    for input_time, expected in time_tests:
        event = CalendlyEvent(
            uri="test", name="Test", email="test@test.de",
            start_time=input_time, end_time=input_time,
            status="active", event_type="Test"
        )
        result = event.date_formatted
        status = "✅" if result == expected else "❌"
        print(f"   {status} {input_time} → {result}")
        if result != expected:
            time_pass = False
    print()
    
    # Test 4: Follow-up calculation
    print("Test 4: Follow-up Berechnung")
    follow_up_tests = [
        ("2024-03-15T10:00:00.000000Z", "2024-03-18"),  # +3 days
        ("2024-12-30T14:00:00.000000Z", "2025-01-02"),  # Year boundary
    ]
    
    follow_pass = True
    for input_time, expected in follow_up_tests:
        event = CalendlyEvent(
            uri="test", name="Test", email="test@test.de",
            start_time=input_time, end_time=input_time,
            status="active", event_type="Test"
        )
        result = event.follow_up_date
        status = "✅" if result == expected else "❌"
        print(f"   {status} {input_time[:10]} → {result} (Expected: {expected})")
        if result != expected:
            follow_pass = False
    print()
    
    # Summary
    results = [test1_pass, status_pass, time_pass, follow_pass]
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
