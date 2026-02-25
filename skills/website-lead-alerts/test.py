#!/usr/bin/env python3
"""Test Website Lead Scraper"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/website-lead-alerts')

from website_leads import Lead, LeadScraper, TelegramNotifier

def run_tests():
    """Test lead scraping and notification logic."""
    print("🧪 Testing Website Lead Scraper...\n")
    
    # Test 1: Lead dataclass
    print("Test 1: Lead Erstellung")
    lead = Lead(
        source="https://example.de/kontakt",
        name="Anna Schmidt",
        email="anna@firma.de",
        phone="+49 30 12345678",
        message="Hallo, ich brauche ein Angebot für eine neue Website. Budget ca. 5000€. Dringend!",
        timestamp="2024-03-15T10:00:00"
    )
    
    print(f"   Name: {lead.name}")
    print(f"   Email: {lead.email}")
    print(f"   Unique ID: {lead.unique_id}")
    print(f"   Summary: {lead.summary}")
    
    test1_pass = (
        lead.name == "Anna Schmidt" and
        lead.email == "anna@firma.de" and
        len(lead.unique_id) == 12
    )
    print(f"   Status: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print()
    
    # Test 2: Priority analysis
    print("Test 2: Prioritäts-Analyse")
    scraper = LeadScraper()
    
    test_leads = [
        {
            'message': 'Nur eine allgemeine Anfrage',
            'expected': 'NORMAL'
        },
        {
            'message': 'Ich benötige ein Angebot für Marketing',
            'expected': 'HOCH'
        },
        {
            'message': 'Dringend! Website Relaunch mit Budget. Angebot sofort!',
            'expected': 'KRITISCH'
        }
    ]
    
    priority_pass = True
    for test in test_leads:
        lead = Lead(source="test", message=test['message'])
        analyzed = scraper._analyze_priority(lead)
        status = "✅" if test['expected'] in analyzed.priority else "❌"
        print(f"   {status} {test['expected']} in {analyzed.priority}")
        if test['expected'] not in analyzed.priority:
            priority_pass = False
    print()
    
    # Test 3: Telegram message formatting
    print("Test 3: Telegram Formatierung")
    notifier = TelegramNotifier("fake-token", "fake-chat")
    
    lead = Lead(
        source="https://meinshop.de/kontakt",
        name="Klaus Weber",
        email="klaus@web.de",
        phone="0171 12345678",
        message="Hallo, ich brauche ein Angebot für einen Onlineshop. Budget ca. 10000€.",
        priority="⚡ HOCH",
        keywords_found=['angebot', 'onlineshop', 'budget']
    )
    lead = LeadScraper()._analyze_priority(lead)  # Re-analyze
    
    msg = notifier.format_message(lead)
    
    checks = [
        'NEUER LEAD' in msg,
        'Klaus Weber' in msg,
        'klaus@web.de' in msg,
        'Onlineshop' in msg,
        'meinshop.de' in msg
    ]
    
    format_pass = all(checks)
    print(f"   ✅ HTML Tags enthalten: {'<b>' in msg and '</b>' in msg}")
    print(f"   ✅ Name enthalten: {'Klaus Weber' in msg}")
    print(f"   ✅ Email enthalten: {'klaus@web.de' in msg}")
    print(f"   ✅ Status: {'✅ PASS' if format_pass else '❌ FAIL'}")
    print()
    
    # Test 4: HTML extraction
    print("Test 4: HTML Lead-Extraktion")
    html = """
    <script>
    window.__INITIAL_STATE__ = {
        "contact": {
            "name": "Max Mustermann",
            "email": "max@test.de",
            "message": "Interesse an Website"
        }
    };
    </script>
    """
    
    leads = scraper.extract_leads_from_html(html, "https://test.de")
    extract_pass = len(leads) == 1 and leads[0].email == "max@test.de"
    
    print(f"   Gefundene Leads: {len(leads)}")
    if leads:
        print(f"   Name: {leads[0].name}")
        print(f"   Email: {leads[0].email}")
    print(f"   Status: {'✅ PASS' if extract_pass else '❌ FAIL'}")
    print()
    
    # Summary
    results = [test1_pass, priority_pass, format_pass, extract_pass]
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
